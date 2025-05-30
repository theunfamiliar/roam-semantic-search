["ideas", "daylist"].forEach(brain => {
  window.roamAlphaAPI.ui.commandPalette.addCommand({
    label: "Run Semantic Query (" + brain.charAt(0).toUpperCase() + brain.slice(1) + ")",
    callback: async () => {
      const blocks = await window.roamAlphaAPI.q(
        '[:find ?uid ?str ?title\n' +
        ' :where\n' +
        ' [?b :block/string ?str]\n' +
        ' [?b :block/uid ?uid]\n' +
        ' [?b :block/page ?p]\n' +
        ' [?p :node/title ?title]\n' +
        ' [(clojure.string/includes? ?str "{{query-singularity:")]\n' +
        ' (not [(clojure.string/includes? ?str "' + '`' + '`' + '`' + '")])\n' +
        ' (not [(= ?title "roam/js")])\n' +
        ']'
      );

      for (let [uid, str, _title] of blocks) {
        const match = str.match(/{{query-singularity:\s*(.+?)}}/);
        if (!match) continue;
        const query = match[1].trim();
        const top_k = 10;

        const loadingUid = window.roamAlphaAPI.util.generateUID();
        await window.roamAlphaAPI.createBlock({
          location: { "parent-uid": uid, order: 0 },
          block: {
            uid: loadingUid,
            string: "⏳ Running " + brain + " query: \"" + query + "\"..."
          }
        });

        try {
          const response = await fetch("https://roam.boomerjihad.com/api/v1/search", {
            method: "POST",
            headers: {
              "Authorization": "Bearer admin-test-token",
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ query, top_k, brain })
          });

          if (!response.ok)
            throw new Error("Status " + response.status + ": " + await response.text());

          const result = await response.json();

          await window.roamAlphaAPI.deleteBlock({ block: { uid: loadingUid } });

          for (let i = 0; i < result.results.length; i++) {
            const item = result.results[i];
            const score = Math.round(item.score * 100);
            await window.roamAlphaAPI.createBlock({
              location: { "parent-uid": uid, order: i + 1 },
              block: { 
                string: `- ((${item.metadata.uid})) ${score}% match\n${item.content}`
              }
            });
          }

          await window.roamAlphaAPI.updateBlock({
            block: {
              uid,
              string: "{{query-singularity: " + query + "}} #queried"
            }
          });
        } catch (err) {
          console.error("❌ Semantic query failed:", err.message);
          await window.roamAlphaAPI.updateBlock({
            block: {
              uid: loadingUid,
              string: "⚠️ Semantic query failed: " + err.message
            }
          });
        }
      }
    }
  });
}); 