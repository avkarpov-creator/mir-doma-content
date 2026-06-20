/* ============================================================
   mir-doma.pro — custom.js
   Едет из git через Git Importer 1.4.2, инлайном перед </body>.
   Делает две вещи:
     1) подгружает шрифты Nunito + Onest (Google Fonts, с preconnect);
     2) включает «появление при прокрутке» для карточек и заголовков.
   ============================================================ */
(function () {
  'use strict';

  /* ── 1. ШРИФТЫ ─────────────────────────────────────────────
     Грузим через <link> (а не @import в CSS) — быстрее и не зависит
     от CSS-оптимизаторов LiteSpeed. */
  function addLink(rel, href, crossorigin) {
    var l = document.createElement('link');
    l.rel = rel;
    l.href = href;
    if (crossorigin) l.crossOrigin = 'anonymous';
    document.head.appendChild(l);
  }
  addLink('preconnect', 'https://fonts.googleapis.com');
  addLink('preconnect', 'https://fonts.gstatic.com', true);
  addLink('stylesheet',
    'https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&family=Onest:wght@400;500;600&display=swap');

  /* ── 2. ПОЯВЛЕНИЕ ПРИ ПРОКРУТКЕ ───────────────────────────
     Уважаем prefers-reduced-motion и наличие IntersectionObserver. */
  var reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;

  function onReady(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }

  onReady(function () {
    /* Класс на <html> включает CSS-правила .reveal — без JS контент видим */
    document.documentElement.classList.add('mdgi-reveal');

    var selector = [
      '.post-card',
      '.post-card-one',
      '.post-card-square',
      '.content-area .page-title',
      '.site-content h2'
    ].join(',');

    var targets = Array.prototype.slice.call(document.querySelectorAll(selector));
    if (!targets.length) return;

    targets.forEach(function (el) { el.classList.add('reveal'); });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    targets.forEach(function (el) { io.observe(el); });
  });
})();
