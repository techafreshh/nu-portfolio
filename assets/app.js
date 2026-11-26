  // --- Theme toggle: manual choice wins, otherwise follow the OS. ---
  (function () {
    var root = document.documentElement;
    var btn = document.getElementById("theme-toggle");
    var moon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
    var sun = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"></path></svg>';
    function current() {
      var saved = null;
      try { saved = localStorage.getItem("theme"); } catch (e) {}
      if (saved === "light" || saved === "dark") return saved;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    function paint() { btn.innerHTML = current() === "dark" ? sun : moon; }
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      paint();
    });
    paint();
  })();

  // --- Name scramble on first paint (subtle, like the reference). ---
  (function () {
    var el = document.getElementById("name");
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var final = el.textContent;
    var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    var start = null, duration = 650;
    function frame(t) {
      if (!start) start = t;
      var p = Math.min((t - start) / duration, 1);
      var reveal = Math.floor(p * final.length);
      var out = final.slice(0, reveal);
      for (var i = reveal; i < final.length; i++) {
        out += final[i] === " " ? " " : chars[Math.floor(Math.random() * chars.length)];
      }
      el.textContent = out;
      if (p < 1) requestAnimationFrame(frame);
      else el.textContent = final;
    }
    requestAnimationFrame(frame);
  })();
