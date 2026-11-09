/* 模考：先选卷，再把题目按 Part 渲染；听力音频吸在题目上方。 */
(function () {
  'use strict';
  var idx = window.DATA_EXAMS || [];
  var paper = document.getElementById('js-paper');
  var picks = {}, submitted = false, current = null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function picker() {
    if (!idx.length) return '';
    return '<div class="picker">' + idx.map(function (it) {
      var hasAudio = it.audio ? '' : ' noaudio';
      return '<button class="pick' + hasAudio + '" data-key="' + it.key + '">' +
        '<b>' + esc(it.title) + '</b>' +
        '<span>' + it.q + ' 题' + (it.audio ? ' · 有音频' : ' · 无音频') +
        (it.graded ? ' · 可判分' : '') + '</span></button>';
    }).join('') + '</div>';
  }

  function load(key) {
    current = key;
    submitted = false; picks = {};
    paper.innerHTML = '<p class="p">载入中…</p>';
    var old = document.getElementById('exam-data');
    if (old) old.remove();
    var s = document.createElement('script');
    s.id = 'exam-data';
    s.src = 'data/exam_' + key + '.js';
    s.onload = function () { window.DATA_EXAM ? render(window.DATA_EXAM) : fail(); };
    s.onerror = fail;
    document.head.appendChild(s);
    document.querySelectorAll('.pick').forEach(function (b) {
      b.classList.toggle('on', b.dataset.key === key);
    });
    history.replaceState(null, '', '?paper=' + key);
  }

  function fail() {
    paper.innerHTML = '<p class="p">这一套的题目数据没找到（可能 PDF 是扫描件，没有文字层）。</p>';
  }

  function countQuestions(d) {
    var n = 0;
    d.parts.forEach(function (p) { p.blocks.forEach(function (b) { if (b.t === 'q' && b.opts.length) n++; }); });
    return n;
  }

  function render(d) {
    document.getElementById('js-title').textContent = d.title + ' · 模考';
    var total = countQuestions(d);
    document.getElementById('js-sub').textContent = total + ' 道选择题' +
      (d.audio ? '，听力音频在题目上方' : '，这一套没有音频') +
      (Object.keys(d.answers || {}).length ? '，可当场判分' : '，答案见真题库的解析');

    var html = '', audioPlaced = false;
    d.parts.forEach(function (part) {
      var hasQ = part.blocks.some(function (b) { return b.t === 'q'; });
      if (!hasQ && part.blocks.length < 2) return;
      html += '<section class="sec"><h2>' + esc(part.name) + '</h2>';
      part.blocks.forEach(function (b) {
        if (b.t === 'q') {
          if (!audioPlaced && d.audio) { html += audioBox(d.audio); audioPlaced = true; }
          html += question(b);
        } else if (b.t === 'h') {
          html += '<h3 class="p" style="color:var(--ink);margin-top:16px">' + esc(b.x) + '</h3>';
        } else {
          var txt = b.x || '';
          var cls = txt.length > 120 ? 'passage' : 'p';
          html += '<p class="' + cls + '">' + esc(txt) + '</p>';
        }
      });
      html += '</section>';
    });
    paper.innerHTML = html;
    bind();
    updateProgress();
  }

  function audioBox(src) {
    return '<div class="audio-box"><div class="t">听力音频 · 与题目同页，边听边做</div>' +
      '<audio controls preload="metadata" src="' + esc(src) + '"></audio>' +
      '<p class="hint">没声音就换 Chrome / Edge；本地没有的走镜像，缓冲几秒。</p></div>';
  }

  function question(q) {
    if (!q.opts.length) {
      // 选词填空 / 段落匹配：填字母，不提供选项
      return '<div class="qwrap" id="q' + q.n + '">' +
        '<div class="qhead"><span class="qno">' + q.n + '</span><span class="qstem">' +
        esc(q.stem || '填字母') + '</span>' +
        '<input class="letter" data-n="' + q.n + '" maxlength="2" placeholder="A–O" aria-label="第 ' + q.n + ' 题答案字母">' +
        '</div></div>';
    }
    var opts = q.opts.map(function (o) {
      return '<div class="opt" data-n="' + q.n + '" data-k="' + o[0] + '"><span class="k">' + o[0] +
        '</span><span>' + esc(o[1]) + '</span><span class="mark"></span></div>';
    }).join('');
    return '<div class="qwrap" id="q' + q.n + '">' +
      '<div class="qhead"><span class="qno">' + q.n + '</span><span class="qstem">' +
      esc(q.stem || '选出最佳答案') + '</span></div><div class="opts">' + opts + '</div></div>';
  }

  function bind() {
    paper.querySelectorAll('.letter').forEach(function (el) {
      el.addEventListener('input', function () {
        if (submitted) return;
        var v = el.value.trim().toUpperCase();
        el.value = v;
        if (v) picks[el.dataset.n] = v; else delete picks[el.dataset.n];
        updateProgress();
      });
    });
    paper.querySelectorAll('.opt').forEach(function (el) {
      el.addEventListener('click', function () {
        if (submitted) return;
        picks[el.dataset.n] = el.dataset.k;
        paper.querySelectorAll('.opt[data-n="' + el.dataset.n + '"]').forEach(function (o) { o.classList.remove('sel'); });
        el.classList.add('sel');
        updateProgress();
      });
    });
  }

  function updateProgress() {
    var total = window.DATA_EXAM ? countQuestions(window.DATA_EXAM) : 0;
    document.getElementById('js-progress').textContent = Object.keys(picks).length + ' / ' + total + ' 已答';
  }

  function submit() {
    var d = window.DATA_EXAM;
    if (!d) return;
    submitted = true;
    var right = 0, answered = Object.keys(picks).length, counted = 0;
    paper.querySelectorAll('.letter').forEach(function (el) {
      var n = el.dataset.n, ans = (d.answers || {})[n];
      if (!ans) return;
      counted++;
      var ok = picks[n] === ans;
      el.classList.add(ok ? 'right' : 'wrong');
      if (ok) right++;
      el.insertAdjacentHTML('afterend', '<span class="mark-inline">' + (ok ? '对' : '答案 ' + ans) + '</span>');
    });
    paper.querySelectorAll('.opt').forEach(function (el) {
      var n = el.dataset.n, k = el.dataset.k, ans = (d.answers || {})[n];
      if (!ans) return;
      counted++;
      el.classList.remove('sel');
      if (k === ans) { el.classList.add('right'); el.querySelector('.mark').textContent = '答案'; }
      else if (picks[n] === k) { el.classList.add('wrong'); el.querySelector('.mark').textContent = '你选'; }
      if (picks[n] === ans) right++;
    });
    var box = document.createElement('div');
    box.className = 'result';
    if (!counted) {
      box.innerHTML = '<b>—</b><span>这一套没有本地答案，对照真题库里的解析 PDF 看</span>';
    } else {
      box.innerHTML = '<b>' + right + '</b><span>对 / 已答 ' + answered + ' 题 · 这套共 ' + counted + ' 题有答案</span>' +
        '<p class="p" style="margin:8px 0 0">绿色是正确答案，红色是你选错的。</p>';
    }
    paper.appendChild(box);
    box.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  document.getElementById('js-submit').addEventListener('click', submit);
  document.getElementById('js-reset').addEventListener('click', function () {
    if (current) load(current);
  });

  document.getElementById('js-picker').innerHTML = picker();
  document.querySelectorAll('.pick').forEach(function (b) {
    b.addEventListener('click', function () { load(b.dataset.key); });
  });

  var q = new URLSearchParams(location.search).get('paper');
  var first = q || (idx.filter(function (i) { return i.audio && i.q; })[0] || idx[0] || {}).key;
  if (first) load(first); else paper.innerHTML = '<p class="p">还没有拆好的卷子。</p>';
})();
