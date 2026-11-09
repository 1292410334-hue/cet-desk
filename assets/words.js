/* 单词本：一次加载一本书，翻卡、标记、错词本。数据以 .js 形式提供，file:// 也能读。 */
(function () {
  'use strict';
  var D = window.Desk, $ = D.$, $$ = D.$$, esc = D.esc;

  var st = { level: 'cet4', idx: 0, mode: 'read', revealed: false, list: [], full: [], coreOnly: false };

  function key(l) { return 'DATA_' + l.toUpperCase(); }

  function load(l) {
    return new Promise(function (res, rej) {
      if (window[key(l)]) return res(window[key(l)]);
      var s = document.createElement('script');
      s.src = 'data/' + l + '.js';
      s.onload = function () { window[key(l)] ? res(window[key(l)]) : rej(new Error('empty')); };
      s.onerror = function () { rej(new Error('missing')); };
      document.head.appendChild(s);
    });
  }

  function pad(n) { n = String(n); return n.length >= 4 ? n : ('000' + n).slice(-4); }

  function render() {
    var w = st.list[st.idx];
    if (!w) return;
    var total = st.list.length;
    var coreSet = (window.DATA_CORE && window.DATA_CORE[st.level]) || [];

    $('#js-idx').textContent = 'No. ' + pad(st.idx + 1);
    var isCore = w.c === 1 || coreSet.indexOf(w.w.toLowerCase()) >= 0;
    $('#js-lv').textContent = D.levelName(st.level) + (isCore ? ' · 核心' : '') +
      (st.mode === 'test' ? ' · 自测' : '');
    $('#js-word').textContent = w.w;

    var phon = [];
    if (w.us) phon.push('<span><b>US</b> /' + esc(w.us) + '/</span>');
    if (w.uk) phon.push('<span><b>UK</b> /' + esc(w.uk) + '/</span>');
    $('#js-phon').innerHTML = phon.join('');

    $('#js-mean').innerHTML = '<ol>' + (w.tr || []).map(function (t) {
      return '<li>' + esc(t) + '</li>';
    }).join('') + '</ol>';

    var d = [];
    if (w.s && w.s.length) {
      d.push('<div><h5>例句</h5>' + w.s.map(function (s) {
        return '<p class="sent">' + esc(s[0]) + (s[1] ? '<em>' + esc(s[1]) + '</em>' : '') + '</p>';
      }).join('') + '</div>');
    }
    if (w.p && w.p.length) {
      d.push('<div><h5>短语</h5><div class="phr">' + w.p.map(function (p) {
        return '<p>' + esc(p[0]) + (p[1] ? ' <i>' + esc(p[1]) + '</i>' : '') + '</p>';
      }).join('') + '</div></div>');
    }
    if (w.y && w.y.length) {
      d.push('<div><h5>同近义</h5><p>' + esc(w.y.join('；')) + '</p></div>');
    }
    $('#js-detail').innerHTML = d.join('');

    var veil = $('#js-veil');
    veil.hidden = !(st.mode === 'test' && !st.revealed);

    $('#js-pos').textContent = (st.idx + 1) + ' / ' + total;
    var mark = D.store.known(st.level)[w.w];
    $('#js-hint').textContent = mark === 'know' ? '上次：认识' : mark === 'again' ? '上次：不熟' : '';

    counts();
  }

  function counts() {
    var total = st.list.length;
    var s = D.store.stats(st.level, total);
    $('#js-know-n').textContent = s.know;
    $('#js-again-n').textContent = s.again;
    $('#js-left-n').textContent = s.left;
    $('#js-prog').style.width = (total ? (s.know / total * 100) : 0) + '%';

    var m = D.store.known(st.level), again = [];
    for (var k in m) { if (m[k] === 'again') again.push(k); }
    var box = $('#js-names');
    if (!again.length) {
      box.innerHTML = '<span style="border:0;padding:0;color:var(--ink-3)">还空着</span>';
    } else {
      box.innerHTML = again.slice(0, 12).map(function (w) {
        return '<span data-w="' + esc(w) + '">' + esc(w) + '</span>';
      }).join('');
      $$('#js-names span').forEach(function (el) {
        el.onclick = function () {
          var i = st.list.findIndex(function (x) { return x.w === el.dataset.w; });
          if (i >= 0) { st.idx = i; st.revealed = false; render(); }
        };
      });
    }
  }

  function letters() {
    var set = {}, out = [];
    st.list.forEach(function (w) {
      var c = w.w[0].toUpperCase();
      if (!set[c]) { set[c] = 1; out.push(c); }
    });
    var cur = (st.list[st.idx] || {}).w || '';
    $('#js-letters').innerHTML = out.map(function (c) {
      var on = cur.charAt(0).toUpperCase() === c ? ' class="on"' : '';
      return '<button' + on + ' data-l="' + c + '">' + c + '</button>';
    }).join('');
    $$('#js-letters button').forEach(function (b) {
      b.onclick = function () {
        var i = st.list.findIndex(function (x) { return x.w[0].toUpperCase() === b.dataset.l; });
        if (i >= 0) { st.idx = i; st.revealed = false; render(); letters(); }
      };
    });
  }

  function scopeLabel() {
    var mode = st.coreOnly ? '核心' : '全部';
    $$('#js-scope button').forEach(function (b) {
      b.textContent = (b.dataset.scope === 'core' ? '核心 ' : '全部 ') +
        (b.dataset.scope === 'core' ? st.full.filter(function (w) { return w.c === 1; }).length : st.full.length);
      b.classList.toggle('on', (b.dataset.scope === 'core') === st.coreOnly);
    });
  }

  function applyScope() {
    st.list = st.coreOnly ? st.full.filter(function (w) { return w.c === 1; }) : st.full.slice();
    st.idx = 0; st.revealed = false;
    scopeLabel(); render(); letters();
  }

  function go(delta) {
    var n = st.list.length;
    if (!n) return;
    st.idx = (st.idx + delta + n) % n;
    st.revealed = false;
    render(); letters();
    D.store.setLast({ level: st.level, idx: st.idx });
  }

  function mark(kind) {
    var w = st.list[st.idx];
    if (!w) return;
    D.store.mark(st.level, w.w, kind);
    if (kind === 'know') D.store.tick();
    go(1);
  }

  function bind() {
    $$('#js-level button').forEach(function (b) {
      b.onclick = function () {
        $$('#js-level button').forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        st.level = b.dataset.level; st.idx = 0; st.revealed = false;
        $('#js-card').style.opacity = '.35';
        load(st.level).then(function (list) {
          st.full = list;
          applyScope();
          $('#js-card').style.opacity = '';
        }).catch(function () {
          $('#js-word').textContent = '数据没找到';
          $('#js-detail').innerHTML = '<p>需要同目录的 <span class="mono">data/' + st.level + '.js</span>。请把整个文件夹一起拷走。</p>';
        });
      };
    });

    $$('#js-scope button').forEach(function (b) {
      b.onclick = function () {
        st.coreOnly = b.dataset.scope === 'core';
        applyScope();
      };
    });

    $$('#js-mode button').forEach(function (b) {
      b.onclick = function () {
        $$('#js-mode button').forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        st.mode = b.dataset.mode; st.revealed = false; render();
      };
    });

    $('#js-card').onclick = function () { if (st.mode === 'test' && !st.revealed) { st.revealed = true; render(); } };
    $('#js-veil').onclick = function (e) { e.stopPropagation(); st.revealed = true; render(); };
    $('#js-know').onclick = function () { mark('know'); };
    $('#js-again').onclick = function () { mark('again'); };
    $('#js-prev').onclick = function () { go(-1); };
    $('#js-next').onclick = function () { go(1); };
    $('#js-shuffle').onclick = function () {
      st.idx = Math.floor(Math.random() * st.list.length);
      st.revealed = false; render(); letters();
    };

    document.addEventListener('keydown', function (e) {
      if (e.target.tagName === 'INPUT') return;
      if (e.key === 'j' || e.key === 'J' || e.key === '1') { mark('know'); }
      else if (e.key === 'k' || e.key === 'K' || e.key === '2') { mark('again'); }
      else if (e.key === ' ') { e.preventDefault(); if (st.mode === 'test' && !st.revealed) { st.revealed = true; render(); } else { go(1); } }
      else if (e.key === 'ArrowLeft') { go(-1); }
      else if (e.key === 'ArrowRight') { go(1); }
    });
  }

  // 启动
  var last = D.store.last();
  st.level = (last && last.level) || 'cet4';
  $$('#js-level button').forEach(function (b) {
    if (b.dataset.level === st.level) b.classList.add('on');
  });
  $$('#js-mode button')[0].classList.add('on');

  bind();
  load(st.level).then(function (list) {
    st.full = list;
    st.list = list.slice();
    scopeLabel();
    st.idx = Math.min((last && last.level === st.level && last.idx) || 0, list.length - 1);
    render(); letters();
  }).catch(function () {
    $('#js-word').textContent = '等等，数据没读到';
    $('#js-detail').innerHTML = '<p>请确认 <span class="mono">data/cet4.js</span> 与页面在同一个文件夹里。</p>';
  });
})();
