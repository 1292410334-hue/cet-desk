/* 听力：清单 + 播放器。本地优先，远程兜底，位置记住。 */
(function () {
  'use strict';
  var D = window.Desk, $ = D.$, $$ = D.$$, esc = D.esc;
  var all = window.DATA_AUDIO || [];
  var audio = $('#js-audio');
  var st = { level: 'cet4', year: 'all', onlyLocal: false, cur: null, rate: 1, loop: false };

  function fmt(t) {
    if (!isFinite(t) || t < 0) t = 0;
    var m = Math.floor(t / 60), s = Math.floor(t % 60);
    return (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
  }
  function short(s) { return s.indexOf('cet4') === 0 ? '四级' : '六级'; }

  function years(list) {
    var out = [];
    list.forEach(function (i) { var y = i.s.slice(0, 4); if (out.indexOf(y) < 0) out.push(y); });
    return out;
  }

  function render() {
    var list = all.filter(function (i) { return i.level === st.level; });
    var ys = years(list.filter(function (i) { return !st.onlyLocal || i.local; }));
    $('#js-years').innerHTML = ['all'].concat(ys).map(function (y) {
      return '<button data-y="' + y + '"' + (st.year === y ? ' class="on"' : '') + '>' +
        (y === 'all' ? '历年' : y) + '</button>';
    }).join('');
    $$('#js-years button').forEach(function (b) {
      b.onclick = function () { st.year = b.dataset.y; render(); };
    });

    var shown = list.filter(function (i) {
      if (st.onlyLocal && !i.local) return false;
      return st.year === 'all' || i.s.indexOf(st.year) === 0;
    });
    $('#js-count').textContent = shown.length + ' 段 · ' + shown.filter(function (i) { return i.local; }).length + ' 段已存本地';

    if (!shown.length) { $('#js-list').innerHTML = '<p class="empty">这一段还没有音频。</p>'; return; }

    var groups = [];
    shown.forEach(function (i) {
      var y = i.s.slice(0, 4);
      var g = groups[groups.length - 1];
      if (!g || g.y !== y) { g = { y: y, rows: [] }; groups.push(g); }
      g.rows.push(i);
    });

    var seq = 0;
    $('#js-list').innerHTML = groups.map(function (g) {
      return '<div class="year-head">' + g.y + '<span>' + g.rows.length + ' 段</span></div>' +
        g.rows.map(function (i) {
          var on = st.cur && st.cur.id === i.id ? ' on' : '';
          seq++;
          return '<div class="track' + on + '" data-id="' + esc(i.id) + '">' +
            '<span class="idx">' + String(seq).padStart(2, '0') + '</span>' +
            '<span class="nm">' + esc(i.n.replace(/\.mp3$/i, '')) +
            (i.local ? '<span class="badge">本地</span>' : '') +
            '<small>' + esc(i.s) + ' · ' + short(i.id) + '</small></span>' +
            '<span class="sz">' + (i.z ? D.size(i.z) : '') + '</span>' +
          '</div>';
        }).join('');
    }).join('');

    $$('.track').forEach(function (el) {
      el.onclick = function () {
        var item = all.filter(function (i) { return i.id === el.dataset.id; })[0];
        if (item) playItem(item);
      };
    });
  }

  function playItem(item) {
    st.cur = item;
    $('#js-player').hidden = false;
    $('#js-title').innerHTML = esc(item.n.replace(/\.mp3$/i, '')) +
      '<small>' + esc(item.s) + ' · ' + short(item.id) + (item.local ? ' · 本地' : ' · 远程') + '</small>';
    audio.src = item.local ? 'data/audio/' + item.local : (item.p || item.u);
    audio.playbackRate = st.rate;
    audio.loop = st.loop;
    var saved = parseFloat(localStorage.getItem('cet.audio.' + item.id) || '0');
    var onLoaded = function () {
      if (saved > 3 && saved < audio.duration - 5) audio.currentTime = saved;
      $('#js-hint').textContent = saved > 3 ? '上次听到 ' + fmt(saved) + '，已接上。' : '';
      audio.removeEventListener('loadedmetadata', onLoaded);
    };
    audio.addEventListener('loadedmetadata', onLoaded);
    audio.play().catch(function () {
      $('#js-hint').textContent = '放不出来：本地没有这个文件，取远程也被挡住了。跑一次 tools/build_audio.py --fetch 就能存到本地。';
    });
    $$('.track').forEach(function (e) { e.classList.toggle('on', e.dataset.id === item.id); });
    setPlayBtn(false);
  }

  function setPlayBtn(playing) {
    var b = $('#js-play');
    b.textContent = playing ? '暂停' : '播放';
    b.classList.toggle('on', playing);
  }

  audio.addEventListener('play', function () { setPlayBtn(true); });
  audio.addEventListener('pause', function () { setPlayBtn(false); });

  audio.addEventListener('timeupdate', function () {
    var d = audio.duration || 0, c = audio.currentTime || 0;
    var p = d ? (c / d * 100) : 0;
    $('#js-fill').style.width = p + '%';
    $('#js-knob').style.left = p + '%';
    $('#js-time').textContent = fmt(c) + ' / ' + fmt(d);
    if (st.cur) {
      if (Math.floor(c) % 5 === 0) localStorage.setItem('cet.audio.' + st.cur.id, String(c));
    }
  });

  audio.addEventListener('error', function () {
    if (!st.cur) return;
    $('#js-hint').innerHTML = '这一段不在本地，远程也没取到（国内多半连不上 GitHub 的音频域名）。' +
      (st.cur.path ? ' <a href="https://github.com/0609x/CET46-Resources/blob/main/' +
        encodeURI(st.cur.path) + '" target="_blank" rel="noopener">在 GitHub 打开</a>' : '') +
      ' · 或跑一次 <span class="mono">python tools/fetch_audio_slow.py</span> 存到本地。';
  });

  $('#js-play').onclick = function () {
    if (!st.cur) return;
    audio.paused ? audio.play() : audio.pause();
  };
  $('#js-back').onclick = function () { audio.currentTime = Math.max(0, audio.currentTime - 15); };
  $('#js-fwd').onclick = function () { audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15); };
  $('#js-speed').onclick = function () {
    var list = [1, 1.25, 1.5, 0.75];
    st.rate = list[(list.indexOf(st.rate) + 1) % list.length];
    audio.playbackRate = st.rate;
    this.textContent = st.rate.toFixed(2).replace(/0$/, '') + '×';
  };
  $('#js-loop').onclick = function () {
    st.loop = !st.loop;
    audio.loop = st.loop;
    this.classList.toggle('on', st.loop);
  };
  $('#js-seek').onclick = function (e) {
    var r = this.getBoundingClientRect();
    var p = (e.clientX - r.left) / r.width;
    if (audio.duration) audio.currentTime = p * audio.duration;
  };

  $$('#js-only button').forEach(function (b) {
    b.onclick = function () {
      $$('#js-only button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      st.onlyLocal = b.dataset.only === 'local';
      st.year = 'all';
      render();
    };
  });

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
