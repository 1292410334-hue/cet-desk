/* 作文批注：规则检查，不联网。词数/段落/连接词/重复/拼写/句长/标点。 */
(function () {
  'use strict';
  var D = window.Desk, $ = D.$, $$ = D.$$, esc = D.esc;
  var st = { level: 'cet4', dict: null };

  var COMMON = ('a an the and or but if because so than then that this these those there here ' +
    'i you he she it we they me him her us them my your his its our their mine yours ' +
    'is am are was were be been being do does did done have has had having will would can could ' +
    'should may might must shall not no nor none nothing nobody none any some all both each every ' +
    'more most much many few little less least very too also just only even still yet already ' +
    'about above across after again against along among around at before behind below beside between ' +
    'beyond by down during for from in inside into near of off on onto out outside over past since ' +
    'through to toward under until up upon with within without as like unlike despite per via ' +
    'what which who whom whose when where why how whether while although though unless whereas ' +
    'one two three four five six seven eight nine ten first second third last next other another ' +
    'good bad big small new old high low long short young great important different possible ' +
    'people person man woman child children student students teacher school college university ' +
    'life time year years day days week month moment way thing things world country city home ' +
    'work job study learn learning make makes made take takes took get gets got give gives gave ' +
    'go goes went come comes came see sees saw look looks looked think thinks thought know knows ' +
    'knew say says said tell tells told find finds found want wants wanted need needs needed ' +
    'use uses used help helps helped show shows showed try tries tried keep keeps kept become ' +
    'becomes became begin begins began bring brings brought buy buys bought call calls called ' +
    'change changes changed choose chose chosen continue decide develop develope effect enjoy ' +
    'expect feel felt follow followed grow grows grew happen happened hear heard hold holds held ' +
    'hope improve include increase keep leave leaves left let live lives lived meet meets met ' +
    'move moves moved offer open opened pay paid play played provide put reach read reading ' +
    'realize receive remain remember require return run runs ran seem seems seemed sell send ' +
    'serve set share sit sits sat speak spoke spoken spend spent stand start started stay ' +
    'stop stopped suggest support talk talked turn turned understand understood wait want watch ' +
    'win won wonder write writes wrote written able afraid almost alone already always animal ' +
    'answer area art ask asked available away baby back ball bank base beat beautiful best ' +
    'better body book born boy break bring build built business busy buy car care carry case ' +
    'cause center certain chance change cheap check choice class clean clear close clothes ' +
    'color common company computer consider control cost country course cover create culture ' +
    'cut dark data deal decide deep describe design detail difficult direct discuss doctor ' +
    'door draw dream drive drop early easy eat education end enough environment example eye ' +
    'face fact family far fast father fear few field fight figure final fine fire five floor ' +
    'food foot force form four free friend front full game garden girl give glass goal gold ' +
    'grow guess hair half hand happy hard head health heart heavy history hotel hour house ' +
    'human hundred idea image imagine indeed information interest island issue join just kind ' +
    'knowledge land language large late laugh law lay lead leader learn letter level lie light ' +
    'line list listen little live local love machine main major manage market matter mean ' +
    'measure media medical meet member memory mention mind minute miss model modern money ' +
    'morning mother music name nation nature near necessary news night note number object ' +
    'occur ocean office often oil order paper part party pass past patient pattern plan plant ' +
    'point police policy poor popular position power practice prepare present president ' +
    'pretty price problem process produce product program project protect public pull purpose ' +
    'quality question quick quiet quite raise rate rather ready real reason record red reduce ' +
    'region relate release report represent resource result rich right rise risk road rock ' +
    'role room rule safe save science score sea season seat second see seem sense service ' +
    'several shape shoot shop short shoulder sign simple simply single sister situation size ' +
    'skill sleep slow small smile social society soft soldier solve son song soon sound space ' +
    'special speak sport spring staff stage stand star state station stay step still stock ' +
    'story street strong structure student style subject success such sudden summer support ' +
    'sure surface system table talk task teach team technology tell term test thank think ' +
    'third though thought thousand threat through throw together tomorrow tonight total touch ' +
    'toward town trade train travel treat tree trip trouble true trust truth try turn type ' +
    'under unit until use usually value various video view village visit voice wait walk wall ' +
    'want war warm watch water wave way wear weather week weight welcome well west what when ' +
    'where whether which while white whole wide wife will win wind window winter wish within ' +
    'without woman wonder word work world worry would write wrong year yes yesterday yet young ' +
    'yourself zero').split(/\s+/);

  var LINKERS = {
    add: ['moreover', 'furthermore', 'in addition', 'besides', 'what is more', 'apart from', 'also'],
    contrast: ['however', 'nevertheless', 'on the contrary', 'in contrast', 'whereas', 'although', 'even though', 'while'],
    cause: ['therefore', 'thus', 'consequently', 'hence', 'as a result', 'because of', 'due to', 'so that'],
    example: ['for example', 'for instance', 'such as', 'namely'],
    order: ['first', 'firstly', 'second', 'secondly', 'finally', 'lastly', 'to begin with'],
    conclude: ['in conclusion', 'to sum up', 'in summary', 'all in all', 'on the whole']
  };

  var STOP = { the: 1, and: 1, to: 1, of: 1, a: 1, in: 1, 'is': 1, 'it': 1, 'that': 1, 'i': 1, 'you': 1, 'we': 1, 'they': 1, 'be': 1, 'for': 1, 'on': 1, 'with': 1, 'as': 1, 'at': 1, 'this': 1, 'but': 1, 'not': 1, 'are': 1, 'was': 1, 'have': 1, 'has': 1, 'can': 1, 'will': 1, 'more': 1, 'my': 1, 'their': 1, 'our': 1 };

  function wordsOf(t) { return (t.match(/[A-Za-z][A-Za-z'’-]*/g) || []); }
  function sentencesOf(t) {
    return t.replace(/([.!?])[ \t]+/g, '$1\u0000').split('\u0000').filter(function (s) { return s.trim(); });
  }

  function load(l) {
    return new Promise(function (res) {
      if (window['DATA_' + l.toUpperCase()]) return res();
      var s = document.createElement('script');
      s.src = 'data/' + l + '.js';
      s.onload = function () { res(); };
      s.onerror = function () { res(); };
      document.head.appendChild(s);
    });
  }

  function dict() {
    if (st.dict) return st.dict;
    var set = {};
    ['CET4', 'CET6'].forEach(function (k) {
      (window['DATA_' + k] || []).forEach(function (w) { set[w.w.toLowerCase()] = 1; });
    });
    COMMON.forEach(function (w) { set[w] = 1; });
    st.dict = set;
    return set;
  }

  function known(word, set) {
    var w = word.toLowerCase().replace(/['’]s$/, '');
    if (set[w]) return true;
    var tries = [w.replace(/s$/, ''), w.replace(/es$/, ''), w.replace(/ed$/, ''), w.replace(/d$/, ''),
      w.replace(/ing$/, ''), w.replace(/ing$/, 'e'), w.replace(/ly$/, ''), w.replace(/er$/, ''),
      w.replace(/est$/, ''), w.replace(/ies$/, 'y'), w.replace(/ied$/, 'y'),
      w.replace(/([bdgklmnprt])\1(ed|ing)$/, '$1$2'), w.replace(/([bdgklmnprt])\1(ed|ing)$/, '$1')];
    for (var i = 0; i < tries.length; i++) { if (tries[i] && set[tries[i]]) return true; }
    return false;
  }

  function check() {
    var text = $('#js-text').value;
    var lvl = st.level;
    var target = lvl === 'cet4' ? 120 : 150;
    var W = wordsOf(text);
    var n = W.length;
    var paras = text.split(/\n\s*\n/).filter(function (p) { return p.trim(); });
    var sents = sentencesOf(text);
    var marks = [];

    if (n < 30) {
      $('#js-marks').innerHTML = '<p class="note" style="font-size:13px">至少写 30 个词再看。现在 ' + n + ' 个。</p>';
      $('#js-score').hidden = true;
      return;
    }

    // 1 长度
    var lenScore, lenNote;
    if (n >= target + 10) { lenScore = 4; lenNote = '词数够。'; }
    else if (n >= target) { lenScore = 3; lenNote = '刚过线，再多写两句更稳。'; }
    else if (n >= target - 25) { lenScore = 2; lenNote = '比要求少 ' + (target - n) + ' 词。'; }
    else { lenScore = 1; lenNote = '明显不够：目标 ' + target + ' 词，现在 ' + n + '。'; }
    marks.push({ tag: tagCls(lenScore >= 3 ? 'good' : 'bad'), tagT: '词数', t: n + ' 词 / 目标 ' + target, n: lenNote });

    // 2 段落
    var pScore = paras.length >= 3 ? 3 : paras.length === 2 ? 2 : 1;
    marks.push({
      tag: tagCls(pScore === 3 ? 'good' : 'bad'), tagT: '段落', t: paras.length + ' 段',
      n: pScore === 3 ? '三段：引入 / 展开 / 收束。' : '建议分三段：开头点题、中间两三个理由、结尾收一句。'
    });

    // 3 连接词
    var hits = {};
    Object.keys(LINKERS).forEach(function (k) {
      LINKERS[k].forEach(function (w) {
        var re = new RegExp('\\b' + w.replace(/\s+/g, '\\s+') + '\\b', 'i');
        if (re.test(text)) hits[w] = k;
      });
    });
    var hCount = Object.keys(hits).length;
    var cScore = hCount >= 4 ? 3 : hCount >= 2 ? 2 : hCount === 1 ? 1 : 0;
    marks.push({
      tag: tagCls(cScore >= 2 ? 'good' : 'bad'), tagT: '连接', t: hCount + ' 处',
      n: hCount ? '用了：' + Object.keys(hits).slice(0, 6).join('、') +
        (hCount < 4 ? '。再多一两个转折或因果。' : '。') : '一个连接词都没用，读起来会像清单。加 however / therefore / for example。'
    });

    // 4 句子长短
    var lens = sents.map(function (s) { return wordsOf(s).length; });
    var avg = lens.length ? Math.round(lens.reduce(function (a, b) { return a + b; }, 0) / lens.length) : 0;
    var longest = Math.max.apply(null, lens.concat([0]));
    var lScore = 3;
    var lNote = '平均 ' + avg + ' 词 / 句，最长 ' + longest + '。';
    if (avg < 8) { lScore = 1; lNote += '句子太碎，试着用 which / because 把两句并起来。'; }
    else if (avg > 26) { lScore = 1; lNote += '句子太长，挑两句拆开。'; }
    else if (longest > 38) { lScore = 2; lNote += '有一句长得离谱，拆。'; }
    marks.push({ tag: tagCls(lScore === 3 ? 'good' : 'bad'), tagT: '句子', t: avg + ' 词 / 句', n: lNote });

    // 5 重复词
    var freq = {};
    W.forEach(function (w) {
      var k = w.toLowerCase();
      if (k.length < 5 || STOP[k]) return;
      freq[k] = (freq[k] || 0) + 1;
    });
    var rep = Object.keys(freq).filter(function (k) { return freq[k] >= 4; })
      .sort(function (a, b) { return freq[b] - freq[a]; }).slice(0, 4);
    if (rep.length) {
      marks.push({
        tag: tagCls('bad'), tagT: '重复', t: rep.map(function (k) { return k + '×' + freq[k]; }).join('，'),
        n: '同一个词反复出现，换同义词或换句式（这个词在单词本能查到同近义）。'
      });
    } else {
      marks.push({ tag: tagCls('good'), tagT: '重复', t: '没有明显重复', n: '' });
    }

    // 6 拼写
    var set = dict();
    var bad = {};
    W.forEach(function (w) {
      if (w.length < 3) return;
      if (/^[A-Z]/.test(w) && w.length > 2) return; // 人名地名先放过
      if (known(w, set)) return;
      bad[w] = (bad[w] || 0) + 1;
    });
    var badList = Object.keys(bad).slice(0, 8);
    var sScore = badList.length === 0 ? 2 : badList.length <= 2 ? 1 : 0;
    marks.push({
      tag: tagCls(sScore === 2 ? 'good' : 'bad'), tagT: '拼写',
      t: badList.length ? badList.join('、') : '没查出问题',
      n: badList.length ? '词库里没有，确认一下是不是拼错或词形不对（也可能是专有名词）。' : ''
    });

    // 7 标点与格式
    var issues = [];
    var cn = text.match(/[，。；：！？（）【】“”]/g);
    if (cn) issues.push('混进了 ' + cn.length + ' 个中文标点（' + Array.from(new Set(cn)).join('') + '），换成英文的');
    var lower = sents.filter(function (s) { var m = s.match(/[A-Za-z]/); return m && m[0] === m[0].toLowerCase(); });
    if (lower.length) issues.push(lower.length + ' 句开头没大写');
    if (/ {2,}/.test(text)) issues.push('有多余空格');
    if (/\s+[,.!?]/.test(text)) issues.push('标点前多了空格');
    if (issues.length) {
      marks.push({ tag: tagCls('bad'), tagT: '格式', t: issues.length + ' 处', n: issues.join('；') + '。' });
    } else {
      marks.push({ tag: tagCls('good'), tagT: '格式', t: '干净', n: '' });
    }

    // 总分：长度4 结构3 连接3 语言3 拼写2 = 15
    var total = lenScore + pScore + cScore + lScore + sScore;
    $('#js-score').hidden = false;
    $('#js-score').innerHTML = '<b>' + total + '</b><span>分 / 15</span>';
    $('#js-marks').innerHTML = marks.map(function (m) {
      return '<div class="mark"><span class="tag ' + m.tag + '">' + m.tagT + '</span>' + esc(m.t) +
        (m.n ? '<em>' + esc(m.n) + '</em>' : '') + '</div>';
    }).join('');
  }

  function tagCls(kind) { return kind === 'good' ? 'good' : 'bad'; }

  function liveCount() {
    var t = $('#js-text').value;
    var n = wordsOf(t).length;
    var p = t.split(/\n\s*\n/).filter(function (x) { return x.trim(); }).length;
    $('#js-count').textContent = n + ' 词 · ' + p + ' 段';
  }

  $('#js-text').addEventListener('input', liveCount);
  $('#js-check').onclick = function () {
    $('#js-marks').innerHTML = '<p class="note" style="font-size:13px">查词库…</p>';
    load(st.level).then(function () { load(st.level === 'cet4' ? 'cet6' : 'cet4').then(check, check); }, check);
  };
  $('#js-clear').onclick = function () {
    $('#js-text').value = '';
    $('#js-marks').innerHTML = '<p class="note" style="font-size:13px">清空了。</p>';
    $('#js-score').hidden = true;
    liveCount();
  };
  $$('#js-level button').forEach(function (b) {
    b.onclick = function () {
      $$('#js-level button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      st.level = b.dataset.level;
    };
  });
  $$('#js-level button')[0].classList.add('on');
  liveCount();
})();
