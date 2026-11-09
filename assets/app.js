/* 公共：存储、日期、顶栏状态。没有依赖。 */
(function (w) {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var K_KNOWN = 'cet.known.';
  var K_DAYS = 'cet.days';
  var K_LAST = 'cet.last';

  function read(k, d) {
    try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); }
    catch (e) { return d; }
  }
  function write(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {}
  }

  var store = {
    known: function (level) { return read(K_KNOWN + level, {}); },
    mark: function (level, word, kind) {
      var m = read(K_KNOWN + level, {});
      if (!kind) { delete m[word]; } else { m[word] = kind; }
      write(K_KNOWN + level, m);
      return m;
    },
    stats: function (level, total) {
      var m = read(K_KNOWN + level, {});
      var know = 0, again = 0;
      for (var k in m) { if (m[k] === 'know') know++; else again++; }
      return { know: know, again: again, total: total || 0, left: Math.max(0, (total || 0) - know) };
    },
    days: function () { return read(K_DAYS, {}); },
    tick: function () {
      var d = store.days(), k = today();
      d[k] = (d[k] || 0) + 1;
      write(K_DAYS, d);
      return d[k];
    },
    streak: function () {
      var d = store.days(), n = 0, t = new Date();
      for (var i = 0; i < 400; i++) {
        var k = ymd(t);
        if (!d[k]) { if (i === 0) { t.setDate(t.getDate() - 1); continue; } break; }
        n++; t.setDate(t.getDate() - 1);
      }
      return n;
    },
    last: function () { return read(K_LAST, null); },
    setLast: function (v) { write(K_LAST, v); }
  };

  function ymd(d) {
    var p = function (n) { return n < 10 ? '0' + n : '' + n; };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }
  function today() { return ymd(new Date()); }

  function cnDate() {
    var d = new Date();
    var wk = '日一二三四五六'[d.getDay()];
    return d.getFullYear() + ' 年 ' + (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日 · 周' + wk;
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function size(n) {
    if (!n) return '';
    if (n > 1048576) return (n / 1048576).toFixed(1) + 'M';
    return Math.round(n / 1024) + 'K';
  }

  function levelName(l) { return l === 'cet6' ? '六级' : '四级'; }

  // 顶栏：当前页高亮 + 日期
  function chrome() {
    var here = location.pathname.split('/').pop() || 'index.html';
    $$('.nav a').forEach(function (a) {
      var href = a.getAttribute('href');
      if (href === here || (here === '' && href === 'index.html')) a.classList.add('on');
    });
    var el = $('#js-date');
    if (el) el.textContent = cnDate();
  }

  // 逐词亮起：每页最多一处，滚到才亮，只亮一次
  function revealWords() {
    var box = document.getElementById('js-reveal');
    if (!box) return;
    var spans = Array.prototype.slice.call(box.querySelectorAll('span'));
    if (!spans.length) return;
    if (!('IntersectionObserver' in window)) {
      spans.forEach(function (s) { s.classList.add('on'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.disconnect();
        spans.forEach(function (s, i) {
          setTimeout(function () { s.classList.add('on'); }, 90 * i);
        });
      });
    }, { threshold: 0.4 });
    io.observe(box);
  }

  document.addEventListener('DOMContentLoaded', function () { chrome(); revealWords(); });

  w.Desk = {
    $: $, $$: $$, store: store, esc: esc, size: size, today: today,
    levelName: levelName, ymd: ymd, cnDate: cnDate
  };
})(window);
