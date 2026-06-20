/* ============================================================
   mir-doma.pro — custom.js
   Едет из git через Git Importer 1.4.2, инлайном перед </body>.
   Делает три вещи:
     1) подгружает шрифты Nunito + Onest (Google Fonts, с preconnect);
     2) строит сезонный герой на главной (body.home) и прячет баннер;
     3) включает «появление при прокрутке» для карточек и заголовков.
   ============================================================ */
(function () {
  'use strict';

  /* ── 1. ШРИФТЫ ─────────────────────────────────────────────*/
  function addLink(rel, href, crossorigin) {
    var l = document.createElement('link');
    l.rel = rel; l.href = href;
    if (crossorigin) l.crossOrigin = 'anonymous';
    document.head.appendChild(l);
  }
  addLink('preconnect', 'https://fonts.googleapis.com');
  addLink('preconnect', 'https://fonts.gstatic.com', true);
  addLink('stylesheet',
    'https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&family=Onest:wght@400;500;600&display=swap');


  /* ── 2. СЕЗОННЫЙ ГЕРОЙ ─────────────────────────────────────
     ⚙️ НАСТРОЙКА: ссылки (url) пока ведут на рубрики-заглушки.
     Заменяй на реальные URL статей по мере публикации — это
     единственное место, которое нужно править. */

  var ICONS = {
    sun:'<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>',
    droplet:'<path d="M12 3.5C12 3.5 6 10 6 14a6 6 0 0 0 12 0c0-4-6-10.5-6-10.5z"/>',
    leaf:'<path d="M5 19c0-7 5-12 14-12 0 9-5 14-12 14a6 6 0 0 1-2-2z"/><path d="M9 15c2-2 4-3 6-4"/>',
    bug:'<rect x="8" y="9" width="8" height="10" rx="4"/><path d="M12 9V6M9.5 6.5 8 5M14.5 6.5 16 5M8 12H5M16 12h3M8 16H5M16 16h3"/>',
    basket:'<path d="M4 10h16l-1.5 9a2 2 0 0 1-2 1.8H7.5a2 2 0 0 1-2-1.8z"/><path d="M8 10 10 4M16 10 14 4M9 14v3M12 14v3M15 14v3"/>',
    snowflake:'<path d="M12 3v18M4.5 7.5l15 9M19.5 7.5l-15 9M12 6l-2-2M12 6l2-2M12 18l-2 2M12 18l2 2"/>',
    seedling:'<path d="M12 21v-7"/><path d="M12 14c0-3 2-5 6-5 0 3-2 5-6 5z"/><path d="M12 16c0-2.5-2-4-5-4 0 2.5 2 4 5 4z"/>',
    flame:'<path d="M12 3c1 3-2 4-2 7a2 2 0 0 0 4 0c0-1-.5-2-.5-2 1.5 1 3 3 3 6a4.5 4.5 0 0 1-9 0c0-4 4.5-5 4.5-11z"/>',
    scissors:'<circle cx="6" cy="7" r="2.5"/><circle cx="6" cy="17" r="2.5"/><path d="M8 8.5 20 17M8 15.5 20 7"/>',
    home:'<path d="M4 11l8-6 8 6"/><path d="M6 10v9h12v-9"/><path d="M10 19v-5h4v5"/>'
  };

  var SEASONS = {
    summer: {
      accent: '#3F7A3A',
      badge: 'Сейчас в сезоне · Лето',
      title: 'Лето в разгаре',
      sub: 'Полив, защита от вредителей и первый урожай — что важно в саду и огороде прямо сейчас.',
      ctaText: 'Что делать летом', ctaUrl: '/category/sad-i-ogorod/',
      motif: ['leaf', 'droplet', 'bug', 'sun'],
      picks: [
        { icon:'bug',     chip:'Защита растений', title:'Как избавиться от тли на растениях', url:'/kak-izbavitsya-ot-tli/' },
        { icon:'droplet', chip:'Полив',           title:'Капельный полив своими руками',      url:'/category/dacha-i-uchastok/' },
        { icon:'leaf',    chip:'Овощи и зелень',   title:'Выращивание огурцов в теплице',      url:'/category/sad-i-ogorod/' }
      ]
    },
    autumn: {
      accent: '#B26C16',
      badge: 'Сейчас в сезоне · Осень',
      title: 'Время урожая',
      sub: 'Сбор, заготовки и подготовка участка к зиме — собрали осенние заботы дачника.',
      ctaText: 'Осенние заботы', ctaUrl: '/category/zagotovki-i-hranenie/',
      motif: ['basket', 'leaf', 'droplet', 'snowflake'],
      picks: [
        { icon:'basket',    chip:'Заготовки', title:'Помидоры на зиму: лучшие рецепты',   url:'/category/zagotovki-i-hranenie/' },
        { icon:'home',      chip:'Хранение',  title:'Как правильно хранить овощи зимой',   url:'/category/zagotovki-i-hranenie/' },
        { icon:'snowflake', chip:'Заморозка', title:'Что можно заморозить на зиму',        url:'/category/zagotovki-i-hranenie/' }
      ]
    },
    winter: {
      accent: '#2F6E5B',
      badge: 'Сейчас в сезоне · Зима',
      title: 'Дача отдыхает — пора планировать',
      sub: 'Утепление, отопление и выбор семян: используем зиму, чтобы подготовиться к новому сезону.',
      ctaText: 'Зимние работы', ctaUrl: '/category/stroitelstvo-i-remont/',
      motif: ['snowflake', 'flame', 'home', 'seedling'],
      picks: [
        { icon:'home',     chip:'Утепление',  title:'Как утеплить дачный дом для зимы', url:'/category/dom-i-uyut/' },
        { icon:'flame',    chip:'Отопление',  title:'Печь для дачи: какую выбрать',     url:'/category/dom-i-uyut/' },
        { icon:'seedling', chip:'Подготовка', title:'Выбор семян: планируем сезон',     url:'/category/sad-i-ogorod/' }
      ]
    },
    spring: {
      accent: '#639922',
      badge: 'Сейчас в сезоне · Весна',
      title: 'Дача просыпается',
      sub: 'Рассада, посадки и обрезка — самое горячее время для сада и огорода уже началось.',
      ctaText: 'Весенние работы', ctaUrl: '/category/sad-i-ogorod/',
      motif: ['seedling', 'scissors', 'sun', 'droplet'],
      picks: [
        { icon:'seedling', chip:'Рассада',     title:'Когда сажать перец на рассаду', url:'/category/sad-i-ogorod/' },
        { icon:'scissors', chip:'Плодовый сад', title:'Обрезка яблони весной',         url:'/category/sad-i-ogorod/' },
        { icon:'leaf',     chip:'Овощи и зелень', title:'Посадка моркови весной',      url:'/category/sad-i-ogorod/' }
      ]
    }
  };

  function currentSeason() {
    var m = new Date().getMonth(); /* 0 = январь */
    if (m === 11 || m <= 1) return 'winter'; /* дек, янв, фев */
    if (m <= 4) return 'spring';             /* мар, апр, май */
    if (m <= 7) return 'summer';             /* июн, июл, авг */
    return 'autumn';                         /* сен, окт, ноя */
  }

  function esc(t) {
    return String(t).replace(/[&<>"]/g, function (c) {
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;' }[c];
    });
  }
  function svg(name) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" ' +
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
           (ICONS[name] || '') + '</svg>';
  }

  function buildHero() {
    if (!document.body.classList.contains('home')) return;
    var content = document.querySelector('#content.site-content') ||
                  document.querySelector('#content');
    if (!content || document.querySelector('.mdgi-home-hero')) return;

    var s = SEASONS[currentSeason()];

    var motif = s.motif.map(svg).join('');
    var picks = s.picks.map(function (p) {
      return '<a class="mdgi-pick" href="' + esc(p.url) + '">' +
               '<div class="mdgi-pick__img">' + svg(p.icon) + '</div>' +
               '<div class="mdgi-pick__body">' +
                 '<span class="mdgi-pick__chip">' + esc(p.chip) + '</span>' +
                 '<p class="mdgi-pick__title">' + esc(p.title) + '</p>' +
               '</div></a>';
    }).join('');

    var wrap = document.createElement('div');
    wrap.className = 'mdgi-home-hero';
    wrap.style.setProperty('--mdgi-accent', s.accent);
    wrap.innerHTML =
      '<div class="mdgi-hero">' +
        '<div class="mdgi-hero__text">' +
          '<span class="mdgi-hero__badge">' + esc(s.badge) + '</span>' +
          '<div class="mdgi-hero__title">' + esc(s.title) + '</div>' +
          '<p class="mdgi-hero__sub">' + esc(s.sub) + '</p>' +
          '<a class="mdgi-hero__cta" href="' + esc(s.ctaUrl) + '">' + esc(s.ctaText) + ' →</a>' +
        '</div>' +
        '<div class="mdgi-hero__motif">' + motif + '</div>' +
      '</div>' +
      '<div class="mdgi-picks">' + picks + '</div>';

    content.insertBefore(wrap, content.firstChild);
  }


  /* ── 3. ПОЯВЛЕНИЕ ПРИ ПРОКРУТКЕ ───────────────────────────*/
  function setupReveal() {
    var reduce = window.matchMedia &&
                 window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce || !('IntersectionObserver' in window)) return;

    document.documentElement.classList.add('mdgi-reveal');

    var selector = [
      '.mdgi-hero', '.mdgi-pick',
      '.post-card', '.post-card-one', '.post-card-square',
      '.content-area .page-title', '.site-content h2'
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
  }


  /* ── ЗАПУСК ────────────────────────────────────────────────*/
  function onReady(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }
  onReady(function () {
    buildHero();   /* герой строится всегда (на главной), без оглядки на анимации */
    setupReveal(); /* появление — только если пользователь не просил их отключить */
  });
})();
