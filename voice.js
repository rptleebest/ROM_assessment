(function () {
  window.romSpeak = function (text) {
    try {
      if (!text || !('speechSynthesis' in window)) return;
      const synth = window.speechSynthesis;
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'ko-KR';
      utter.rate = 0.95;
      utter.pitch = 1.0;
      utter.volume = 1.0;
      // Do not cancel every time; queueing helps sequential instructions.
      synth.speak(utter);
    } catch (e) {
      console.log('romSpeak error', e);
    }
  };
})();
