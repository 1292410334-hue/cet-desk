/* 考点练习：从真实词条出四种题，当场判分。 */
(function () {
  'use strict';
  var D = window.Desk, $ = D.$, $$ = D.$$, esc = D.esc;
  var st = { level: 'cet4', n: 20, qs: [], answered: 0, right: 0, list: [] };

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

  function pick(arr, n) {
    var a = arr.slice(), out = [];
    while (a.length && out.length < n) out.push(a.splice(Math.floor(Math.random() * a.length), 1)[0]);
    return out;
  }
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function firstMean(w) { return (w.tr && w.tr[0]) || ''; }
  function hintOf(w) { return w[0] + ' ' + w.slice(1).replace(/[A-Za-z]/g, '_').split('').join(' '); }

  // 四类题
  function qMean(w, pool) {
    var others = pick(pool.filter(function (x) { return x.w !== w.w && firstMean(x) !== firstMean(w); }), 3);
    if (others.length < 3) return null;
    var opts = shuffle([firstMean(w)].concat(others.map(firstMean)));
    return {
      type: '词义', word: w, stem: '「<span class="w">' + esc(w.w) + '</span>」的意思是',
      opts: opts.map(function (t) { return { t: t, ok: t === firstMean(w) }; }), answer: firstMean(w)
    };
  }
  function qPhon(w, pool) {
    if (!w.us) return null;
    var others = pick(pool.filter(function (x) { return x.w !== w.w; }), 3);
    var opts = shuffle([w.w].concat(others.map(function (x) { return x.w; })));
    return {
      type: '音标', word: w, stem: '<span class="mono">/' + esc(w.us) + '/</span> 是哪个词',
      opts: opts.map(function (t) { return { t: t, ok: t.toLowerCase() === w.w.toLowerCase() }; }), answer: w.w
    };
  }
  function qPhrase(w, pool) {
    if (!w.p || !w.p.length) return null;
    var ph = w.p[Math.floor(Math.random() * w.p.length)];
    var en = ph[0], cn = ph[1] || '';
    var cand = pool.filter(function (x) { return x.w !== w.w && x.p && x.p.length; });
    if (cand.length < 3) cand = pool.filter(function (x) { return x.w !== w.w; });
    var others = pick(cand, 3);
    var opts = shuffle([w.w].concat(others.map(function (x) { return x.w; })));
    return {
      type: '搭配', word: w, stem: esc(en.replace(new RegExp(w.w, 'i'), '＿＿')) + (cn ? '<small style="color:var(--ink-3)"> ' + esc(cn) + '</small>' : ''),
      opts: opts.map(function (t) { return { t: t, ok: t.toLowerCase() === w.w.toLowerCase() }; }), answer: w.w
    };
  }
  function qSpell(w) {
    var m = firstMean(w);
    if (!m) return null;
    return {
      type: '拼写', word: w, spell: true,
      stem: '写出这个词：<small style="color:var(--ink-3)">' + esc(m) + '</small>' +
        '<small style="color:var(--ink-3);font-family:var(--mono);letter-spacing:.14em"> · ' + esc(hintOf(w.w)) + '</small>',
      answer: w.w
    };
  }

  function build(list, n) {
    var pool = list.filter(function (w) { return w.tr && w.tr.length && w.w.length > 1; });
    var picked = pick(pool, n * 2);
    var qs = [];
    var makers = [qMean, qPhon, qPhrase, qSpell];
    var mi = 0;
    for (var i = 0; i < picked.length && qs.length < n; i++) {
      var w = picked[i];
      var q = null;
      for (var t = 0; t < makers.length && !q; t++) {
        q = makers[(mi + t) % makers.length](w, pool);
      }
      if (q) { qs.push(q); mi = (mi + 1) % makers.length; }
    }
    return qs;
  }

  function render() {
    var box = $('#js-qs');
    if (!st.qs.length) {
      box.innerHTML = '<p class="empty">点「换一轮」开始。</p>';
      $('#js-cells').innerHTML = '';
      return;
    }
    box.innerHTML = st.qs.map(function (q, i) {
      var body;
      if (q.spell) {
        body = '<input class="spell" data-i="' + i + '" placeholder="' + q.word.w.length + ' 个字母" autocomplete="off" spellcheck="false">';
      } else {
        body = '<div class="opts">' + q.opts.map(function (o, k) {
          return '<div class="opt" data-i="' + i + '" data-k="' + k + '"><span class="k">' +
            'ABCD'[k] + '</span><span>' + esc(o.t) + '</span></div>';
        }).join('') + '</div>';
      }
      return '<div class="q" id="q' + i + '">' +
        '<div class="qno">' + String(i + 1).padStart(2, '0') + ' · ' + q.type + '</div>' +
        '<div class="stem">' + q.stem + '</div>' + body +
        '<div class="explain" hidden></div></div>';
    }).join('');

    $$('.opt').forEach(function (el) {
      el.onclick = function () { answer(+el.dataset.i, +el.dataset.k, el); };
    });
    $$('.spell').forEach(function (el) {
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { answerSpell(+el.dataset.i, el); }
      });
    });
    drawCells();
    updateStatus();
  }

  function explain(q, ok) {
    var w = q.word, s = (w.s && w.s[0]) ? w.s[0] : null;
    var html = '<b>' + (ok ? '对。' : '答案是 ') + esc(q.answer) + '</b>';
    if (firstMean(w)) html += ' · ' + esc(firstMean(w));
    if (s) html += '<em>' + esc(s[0]) + (s[1] ? ' · ' + esc(s[1]) : '') + '</em>';
    return html;
  }

  function markWord(q, ok) {
    D.store.mark(st.level, q.word.w, ok ? 'know' : 'again');
  }

  function finishOne(i, ok, q) {
    q.ok = ok;
    var box = $('#q' + i);
    var exp = box.querySelector('.explain');
    exp.hidden = false;
    exp.innerHTML = explain(q, ok);
    st.answered++;
    if (ok) st.right++;
    markWord(q, ok);
    drawCells();
    updateStatus();
    if (st.answered === st.qs.length) showScore();
  }

  function answer(i, k, el) {
    var q = st.qs[i];
    if (q.done) return;
    q.done = true;
    var ok = !!q.opts[k].ok;
    var opts = el.parentNode.querySelectorAll('.opt');
    Array.prototype.forEach.call(opts, function (o, idx) {
      if (q.opts[idx].ok) o.classList.add('ok');
      else if (o === el) o.classList.add('no');
      o.style.pointerEvents = 'none';
    });
    finishOne(i, ok, q);
  }

  function answerSpell(i, el) {
    var q = st.qs[i];
    if (q.done) return;
    q.done = true;
    el.dataset.done = '1';
    var val = el.value.trim().toLowerCase();
    var ok = val === q.word.w.toLowerCase();
    el.style.borderColor = ok ? 'rgba(61,90,76,.6)' : 'rgba(163,58,44,.6)';
    el.style.color = ok ? 'var(--green)' : 'var(--red)';
    el.disabled = true;
    finishOne(i, ok, q);
  }

  function drawCells() {
    $('#js-cells').innerHTML = st.qs.map(function (q, i) {
      var cls = q.done ? (q.ok ? 'right' : 'wrong') : '';
      return '<i class="' + cls + '">' + (i + 1) + '</i>';
    }).join('');
  }

  function updateStatus() {
    $('#js-status').textContent = st.qs.length
      ? '已答 ' + st.answered + ' / ' + st.qs.length + ' · 对 ' + st.right
      : '还没开始';
  }

  function showScore() {
    var rate = Math.round(st.right / st.qs.length * 100);
    $('#js-score').innerHTML = '<b>' + rate + '</b> 分<br>' +
      '对 ' + st.right + ' · 错 ' + (st.qs.length - st.right) + '<br>' +
      '<button class="btn ghost" id="js-again" style="margin-top:10px;padding:4px 12px;font-size:12px">再来一轮</button>';
    $('#js-again').onclick = start;
  }

  function start() {
    $('#js-qs').innerHTML = '<p class="empty">出题中…</p>';
    load(st.level).then(function (list) {
      st.list = list;
      st.qs = build(list, st.n);
      st.answered = 0; st.right = 0;
      render();
    }).catch(function () {
      $('#js-qs').innerHTML = '<p class="empty">没读到词库：需要 data/' + st.level + '.js。</p>';
    });
  }

  $$('#js-level button').forEach(function (b) {
    b.onclick = function () {
      $$('#js-level button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      st.level = b.dataset.level; start();
    };
  });
  $$('#js-num button').forEach(function (b) {
    b.onclick = function () {
      $$('#js-num button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      st.n = +b.dataset.n; start();
    };
  });
  $('#js-new').onclick = start;
  $$('#js-level button')[0].classList.add('on');

  // 打开就出一轮，省一次点击
  start();
})();
