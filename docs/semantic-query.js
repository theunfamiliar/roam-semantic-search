const registerSemanticQuery = () => {
    console.log("✅ semantic-query.js loaded"); // confirm script load
  
    const handler = async (context) => {
      console.log("🧠 Handler triggered"); // confirm SmartBlock command triggered
  
      const query = context.text || "What do I believe about control?";
  
      const response = await fetch("http://localhost:8000/semantic-search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Basic " + btoa("admin:secret")
        },
        body: JSON.stringify({
          query,
          top_k: 5,
          mode: "Next RAP",
          rhyme_sound: null
        })
      });
  
      if (!response.ok) {
        return [`❌ Error: ${response.status} ${response.statusText}`];
      }
  
      const result = await response.json();
      return [result.answer, ...result.blocks];
    };
  
    const command = { text: "SEMANTICQUERY", handler };
  
    if (window.roamjs?.extension?.smartblocks) {
      window.roamjs.extension.smartblocks.registerCommand(command);
    } else {
      document.body.addEventListener("roamjs:smartblocks:loaded", () =>
        window.roamjs.extension.smartblocks.registerCommand(command)
      );
    }
  };
  
  registerSemanticQuery();