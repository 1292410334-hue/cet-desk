/* 真题库：按考次列出原卷 / Word / 答案 / 听力，链接指向 GitHub 原件。 */
(function () {
  'use strict';
  var D = window.Desk, $ = D.$, $$ = D.$$, esc = D.esc;
  var data = window.DATA_PAPERS || null;
  var st = { level: 'cet4', year: 'all' };

  var KIND = { '真题PDF': '真题', '真题Word': 'Word', '答案解析': '答案', '听力音频': '听力' };
  var CN = { '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六' };

  // 从文件名里取「第几套」：第1套 / （一） / _2025_12_1 / 卷一
  function numeral(name) {
    var pats = [
      /第\s*([一二三四五六1-6])\s*套/,
      /[（(]\s*([一二三四五六1-6])\s*[)）]/,
      /_(\d{4})_(\d{2})_([1-6])(?:_ans)?/,
      /卷\s*([一二三四五六1-6])/
    ];
    for (var i = 0; i < pats.length; i++) {
      var m = name.match(pats[i]);
      if (m) return CN[m[m.length - 1]] || m[m.length - 1];
    }
    return '';
  }

  function chip(item) {
    var n = numeral(item.n);
    var label = n ? '卷' + n : (item.k === '听力音频' ? '音频' : item.k === '答案解析' ? '参考' : '全本');
    if (item.e === 'md') label = '参考';
    var title = item.k + ' · ' + item.n + (item.z ? ' · ' + D.size(item.z) : '');
    if (item.l) {
      // 已经拆成题目的那一套，直接进模考页
      if (item.n === 'cet6_2026_06_1.pdf') {
        return '<a class="local" href="exam.html" title="站内模考 · ' + esc(title) + '">' +
          esc(label) + '<i>考</i></a>';
      }
      var isPage = /\.html?$/i.test(item.l);
      var href = isPage
        ? 'viewer.html?f=' + encodeURIComponent(item.l) + '&t=' + encodeURIComponent(item.n) + '&k=' + encodeURIComponent(item.k)
        : item.l;
      var target = isPage ? '' : ' target="_blank" rel="noopener"';
      return '<a class="local" href="' + esc(href) + '"' + target + ' title="本地文件 · ' + esc(title) + '">' +
        esc(label) + '<i>本</i></a>';
    }
    // 远程文件也走镜像，国内能打开
    var raw = item.u.replace('/blob/main/', '/main/')
      .replace('https://github.com/', 'https://raw.githubusercontent.com/');
    var href2 = 'https://gh-proxy.com/' + raw;
    return '<a href="' + esc(href2) + '" target="_blank" rel="noopener" title="镜像打开 · ' + esc(title) + '">' +
      esc(label) + '</a>';
  }

  function groups(items) {
    var order = ['真题PDF', '真题Word', '答案解析', '听力音频'];
    var buckets = {};
    items.forEach(function (i) { (buckets[i.k] = buckets[i.k] || []).push(i); });
    return order.filter(function (k) { return buckets[k]; }).map(function (k) {
      return '<span class="kblock"><b class="kl">' + KIND[k] + '</b>' +
        buckets[k].map(chip).join('') + '</span>';
    }).join('');
  }

  function years(list) {
    var ys = [];
    list.forEach(function (x) {
      var y = x.s.slice(0, 4);
      if (ys.indexOf(y) < 0) ys.push(y);
    });
    return ys;
  }

  function render() {
    if (!data) {
      $('#js-list').innerHTML = '<p class="empty">没有读到真题清单（data/papers.js）。</p>';
      return;
    }
    var list = data.levels[st.level] || [];
    var shown = list.filter(function (x) { return st.year === 'all' || x.s.indexOf(st.year) === 0; });

    $('#js-years').innerHTML = ['all'].concat(years(list)).map(function (y) {
      var t = y === 'all' ? '全部' : y;
      return '<button data-year="' + y + '"' + (st.year === y ? ' class="on"' : '') + '>' + t + '</button>';
    }).join('');
    $$('#js-years button').forEach(function (b) {
      b.onclick = function () { st.year = b.dataset.year; render(); };
    });

    var files = shown.reduce(function (n, x) { return n + x.i.length; }, 0);
    var loc = shown.reduce(function (n, x) { return n + x.i.filter(function (i) { return i.l; }).length; }, 0);
    $('#js-count').textContent = shown.length + ' 个考次 · ' + files + ' 份文件' + (loc ? ' · 本地 ' + loc : '');

    if (!shown.length) {
      $('#js-list').innerHTML = '<p class="empty">这一年还没有。</p>';
      return;
    }

    // 按年份分组，年份做大标题
    var groupsByYear = [];
    shown.forEach(function (x) {
      var y = x.s.slice(0, 4);
      var g = groupsByYear[groupsByYear.length - 1];
      if (!g || g.y !== y) { g = { y: y, rows: [] }; groupsByYear.push(g); }
      g.rows.push(x);
    });

    $('#js-list').innerHTML = groupsByYear.map(function (g) {
      var n = g.rows.reduce(function (a, x) { return a + x.i.length; }, 0);
      var head = '<div class="year-head">' + g.y + '<span>' + g.rows.length + ' 个考次 · ' + n + ' 份</span></div>';
      return head + g.rows.map(function (x) {
        var m = x.s.slice(5);
        var sub = { '03': '3 月 · 加考', '06': '6 月', '09': '9 月 · 加考', '12': '12 月' }[m] || m + ' 月';
        return '<div class="paper-row">' +
          '<div class="when">' + esc(x.s) + '<small>' + esc(sub) + ' · ' + x.i.length + ' 份</small></div>' +
          '<div class="files">' + groups(x.i) + '</div>' +
        '</div>';
      }).join('');
    }).join('');
  }

  $$('#js-level button').forEach(function (b) {
    b.onclick = function () {
      $$('#js-level button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      st.level = b.dataset.level; st.year = 'all'; render();
    };
  });
  $$('#js-level button')[0].classList.add('on');
  render();
})();
