/* Davis Landworks, davislandworksva.com: the estimate form, the phone action bar and the photo viewer.
   Loaded by every page. The business facts (phone, email), the lead API base and the Turnstile key come from
   data attributes on the form, which the build fills from _build/site.json; nothing is typed in here. */

/* Estimate form.
   Text path (phones, and every device while no lead API is configured): builds a text message to Harrison and
   opens it. With the API configured, a copy of the fields goes to the beacon route just before the text opens.
   Send path (computers with the API configured, or a phone that chooses "send it from here"): posts the request,
   uploads up to six photos resized on the device, then shows a reference number. If anything fails, the visitor
   gets the phone number and a prefilled email instead. With no API configured, nothing is ever posted. */
(function () {
  var form = document.getElementById('estimate-form');
  if (!form) return;
  var attr = function (n) { return (form.getAttribute('data-' + n) || '').trim(); };
  var PHONE = attr('phone'), EMAIL = attr('email'), API = attr('lead-api').replace(/\/+$/, ''), TS_KEY = attr('turnstile-key');
  var MAX_PHOTOS = 6, MAX_EDGE = 1600, JPEG_QUALITY = 0.85;
  var canText = window.matchMedia('(hover: none) and (pointer: coarse)').matches || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (sel) { return form.querySelector(sel); };
  var radios = Array.prototype.slice.call(form.querySelectorAll('input[name="cservice"]'));
  var error = document.getElementById('form-error');
  var fallback = $('.form-fallback'), failed = $('.form-failed'), done = $('.form-done');
  var submit = $('button[type="submit"]'), label = $('.submit-label');
  var photoField = $('.photo-field'), photoInput = form.elements.cphotos, photoList = $('.photo-progress'), photoCount = $('.photo-count');
  var progress = $('.form-progress'), sendSwitch = $('.send-switch');
  var mode = 'text';

  function chosen() { return radios.filter(function (x) { return x.checked; })[0] || null; }
  function serviceLabel() { var r = chosen(); return r ? r.value : ''; }
  function serviceKey() { var r = chosen(); return (r && r.getAttribute('data-service')) || 'other'; }

  Array.prototype.slice.call(document.querySelectorAll('[data-choose]')).forEach(function (b) {
    b.addEventListener('click', function (e) {
      e.preventDefault();
      var name = b.getAttribute('data-choose');
      radios.forEach(function (r) { r.checked = r.value === name; });
      var est = document.getElementById('estimate'), set = form.querySelector('fieldset');
      var room = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
      var fits = set.getBoundingClientRect().bottom - est.getBoundingClientRect().top + room <= window.innerHeight;
      (fits ? est : set).scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
      var r = chosen();
      if (r) setTimeout(function () { r.focus({ preventScroll: true }); }, reduce ? 0 : 500);
    });
  });

  /* Where the visitor came from: the referring site's host and any utm_source and utm_medium on the landing URL,
     kept for the session so they survive a click to another page of this site. */
  var src = { referrer_host: '', utm_source: '', utm_medium: '' };
  try {
    var kept = JSON.parse(sessionStorage.getItem('dl-src') || 'null');
    if (kept && typeof kept === 'object') src = { referrer_host: String(kept.referrer_host || ''), utm_source: String(kept.utm_source || ''), utm_medium: String(kept.utm_medium || '') };
  } catch (e) {}
  try {
    var q = new URLSearchParams(window.location.search);
    if (q.get('utm_source')) { src.utm_source = q.get('utm_source').slice(0, 80); src.utm_medium = (q.get('utm_medium') || '').slice(0, 80); }
    if (document.referrer && !src.referrer_host) {
      var host = new URL(document.referrer).hostname;
      if (host && host !== window.location.hostname) src.referrer_host = host.slice(0, 120);
    }
    sessionStorage.setItem('dl-src', JSON.stringify(src));
  } catch (e) {}

  var LABELS = { cname: 'your name', cphone: 'a mobile number with 10 digits', caddress: 'the job address' };
  var MESSAGES = { cname: 'Please add your name.', cphone: 'Please add a mobile number with 10 digits, area code first.', caddress: 'Please add the job address.' };
  var fields = ['cname', 'cphone', 'caddress'].map(function (n) { return form.elements[n]; });

  /* Keep only the digits and drop a leading US country code, so (757) 555-0123, 757.555.0123 and +1 757 555 0123 all count as 10. */
  function digits(val) {
    var d = val.replace(/\D/g, '');
    return d.length === 11 && d.charAt(0) === '1' ? d.slice(1) : d;
  }
  function problem(el) {
    var val = el.value.trim();
    if (el.required && !val) return true;
    if (el.name === 'cphone' && digits(val).length !== 10) return true;
    return false;
  }
  function mark(el, bad) {
    el.setAttribute('aria-invalid', bad ? 'true' : 'false');
    document.getElementById('err-' + el.name).textContent = bad ? MESSAGES[el.name] : '';
  }
  function listText(parts) { return parts.length > 1 ? parts.slice(0, -1).join(', ') + ' and ' + parts[parts.length - 1] : parts[0]; }
  function sayMissing(list) { return list.length ? 'Please add ' + listText(list.map(function (f) { return LABELS[f.name]; })) + '.' : ''; }

  fields.forEach(function (el) {
    ['input', 'change'].forEach(function (type) {
      el.addEventListener(type, function () {
        if (el.getAttribute('aria-invalid') === 'true' && !problem(el)) {
          mark(el, false);
          error.textContent = sayMissing(fields.filter(function (f) { return f.getAttribute('aria-invalid') === 'true'; }));
        }
      });
    });
  });

  function val(n) { var el = form.elements[n]; return el ? String(el.value || '').trim() : ''; }
  function payload() {
    return {
      name: val('cname'), phone: digits(val('cphone')), address: val('caddress'), service: serviceKey(), size: val('csize'),
      day: val('cdate'), details: val('cdetails'), referrer_host: src.referrer_host, utm_source: src.utm_source,
      utm_medium: src.utm_medium, website: val('website')
    };
  }
  function textMessage() {
    var lines = ['Hi Harrison, I would like a free estimate.'];
    if (serviceLabel()) lines.push('Service: ' + serviceLabel());
    lines.push('Name: ' + val('cname'), 'Phone: ' + val('cphone'), 'Job address: ' + val('caddress'));
    if (val('csize')) lines.push('Stump size: ' + val('csize'));
    if (val('cdate')) lines.push('Preferred day: ' + val('cdate'));
    if (val('cdetails')) lines.push('Details: ' + val('cdetails'));
    return lines.join('\n');
  }
  function setMail(message) {
    var href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent('Estimate request') + '&body=' + encodeURIComponent(message);
    Array.prototype.slice.call(form.querySelectorAll('.fallback-mail')).forEach(function (a) { a.href = href; });
  }

  /* text mode builds a text message; send mode posts to the lead API */
  function setMode(next) {
    mode = next;
    form.setAttribute('data-mode', mode);
    label.textContent = mode === 'send' ? 'Send to Harrison' : 'Start a text to Harrison';
    photoField.hidden = mode !== 'send';
    if (sendSwitch) sendSwitch.hidden = mode === 'send' || !(API && canText);
    if (mode === 'send') loadTurnstile();
  }
  Array.prototype.slice.call(form.querySelectorAll('[data-switch-send]')).forEach(function (b) {
    b.addEventListener('click', function () {
      fallback.hidden = true;
      setMode('send');
      photoField.scrollIntoView({ block: 'nearest', behavior: reduce ? 'auto' : 'smooth' });
      (photoInput || submit).focus({ preventScroll: true });
    });
  });
  if (photoInput) photoInput.addEventListener('change', function () {
    var n = photoInput.files ? photoInput.files.length : 0;
    photoCount.textContent = !n ? '' : n > MAX_PHOTOS ? 'Only the first ' + MAX_PHOTOS + ' photos will be sent.' : n + (n === 1 ? ' photo chosen.' : ' photos chosen.');
  });
  var tryAgain = $('.try-again');
  if (tryAgain) tryAgain.addEventListener('click', function () { failed.hidden = true; submit.focus(); });

  /* Turnstile: loaded only in send mode and only when a site key is set. The challenge runs at submit time. */
  var ts = { widget: null, waiting: null, failed: false };
  window.dlTurnstileReady = function () {
    try {
      ts.widget = window.turnstile.render($('.turnstile-box'), {
        sitekey: TS_KEY, execution: 'execute', appearance: 'interaction-only',
        callback: function (t) { if (ts.waiting) ts.waiting(t); },
        'error-callback': function () { if (ts.waiting) ts.waiting(''); return true; },
        'timeout-callback': function () { if (ts.waiting) ts.waiting(''); },
        'expired-callback': function () {}
      });
    } catch (e) { ts.failed = true; }
  };
  function loadTurnstile() {
    if (!TS_KEY || document.getElementById('turnstile-script')) return;
    var s = document.createElement('script');
    s.id = 'turnstile-script';
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=dlTurnstileReady';
    s.async = true;
    s.onerror = function () { ts.failed = true; };
    document.head.appendChild(s);
  }
  function whenWidget() {
    return new Promise(function (resolve) {
      var tries = 0;
      (function poll() {
        if (ts.widget !== null || ts.failed || !TS_KEY || tries++ > 24) return resolve();
        setTimeout(poll, 250);
      })();
    });
  }
  function token() {
    return whenWidget().then(function () {
      return new Promise(function (resolve) {
        if (!TS_KEY || ts.failed || !window.turnstile || ts.widget === null) return resolve('');
        var finished = false;
        var finish = function (t) { if (finished) return; finished = true; ts.waiting = null; resolve(t || ''); };
        ts.waiting = finish;
        try { window.turnstile.reset(ts.widget); window.turnstile.execute(ts.widget); } catch (e) { finish(''); }
        setTimeout(function () { finish(''); }, 30000);
      });
    });
  }

  function request(method, url, body, headers, onProgress) {
    return new Promise(function (resolve, reject) {
      var x = new XMLHttpRequest();
      x.open(method, url, true);
      x.timeout = 90000;
      Object.keys(headers || {}).forEach(function (k) { x.setRequestHeader(k, headers[k]); });
      if (onProgress && x.upload) x.upload.onprogress = function (e) { if (e.lengthComputable && e.total) onProgress(e.loaded / e.total); };
      x.onload = function () {
        if (x.status < 200 || x.status >= 300) return reject(new Error('HTTP ' + x.status));
        var data = null;
        try { data = JSON.parse(x.responseText || 'null'); } catch (e) {}
        resolve(data && typeof data === 'object' ? data : {});
      };
      x.onerror = x.ontimeout = x.onabort = function () { reject(new Error('network')); };
      x.send(body);
    });
  }

  /* Photos: redrawn on a canvas at about 1600 px on the long side and re-encoded as JPEG, which also drops the
     EXIF block (location, camera, time) the original carried. */
  function shrink(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file), img = new Image();
      img.onload = function () {
        URL.revokeObjectURL(url);
        var w = img.naturalWidth, h = img.naturalHeight;
        if (!w || !h) return reject(new Error('empty'));
        var s = Math.min(1, MAX_EDGE / Math.max(w, h));
        var c = document.createElement('canvas');
        c.width = Math.max(1, Math.round(w * s));
        c.height = Math.max(1, Math.round(h * s));
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        c.toBlob(function (b) { if (b) resolve(b); else reject(new Error('encode')); }, 'image/jpeg', JPEG_QUALITY);
      };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('decode')); };
      img.src = url;
    });
  }
  function photoRow(i, text) { var li = photoList.children[i]; if (li) li.textContent = 'Photo ' + (i + 1) + ': ' + text; }
  function uploadPhotos(ref, uploadToken) {
    var files = photoInput && photoInput.files ? Array.prototype.slice.call(photoInput.files, 0, MAX_PHOTOS) : [];
    var sent = 0;
    photoList.innerHTML = '';
    files.forEach(function (f, i) { var li = document.createElement('li'); li.textContent = 'Photo ' + (i + 1) + ': waiting'; photoList.appendChild(li); });
    photoList.hidden = !files.length;
    return files.reduce(function (chain, file, i) {
      return chain.then(function () {
        photoRow(i, 'preparing');
        return shrink(file).then(function (blob) {
          return request('PUT', API + '/api/lead/' + encodeURIComponent(ref) + '/photo/' + (i + 1), blob,
            { 'Content-Type': 'image/jpeg', 'Authorization': 'Bearer ' + uploadToken },
            function (p) { photoRow(i, Math.round(p * 100) + '%'); });
        }).then(function () { sent++; photoRow(i, 'sent'); }, function () { photoRow(i, 'did not go through'); });
      });
    }, Promise.resolve()).then(function () { return { sent: sent, total: files.length }; });
  }

  function say(text) { progress.textContent = text; progress.hidden = !text; }
  function busy(on) {
    submit.disabled = on;
    form.classList.toggle('is-busy', on);
    if (on) label.textContent = 'Sending'; else setMode(mode);
  }
  function finish(ref, n) {
    done.querySelector('.done-ref').textContent = ref;
    var note = done.querySelector('.done-photos');
    note.textContent = !n.total ? '' : n.sent === n.total ? (n.total === 1 ? 'Your photo came through.' : 'All ' + n.total + ' photos came through.')
      : n.sent + ' of ' + n.total + ' photos came through. Text the rest to Harrison if you can.';
    note.hidden = !note.textContent;
    form.classList.add('is-done');
    done.hidden = false;
    done.focus();
  }
  function send(p) {
    var ref = '', upload = '';
    busy(true);
    say('Sending your request.');
    token().then(function (t) {
      p.turnstile_token = t;
      return request('POST', API + '/api/lead', JSON.stringify(p), { 'Content-Type': 'application/json' });
    }).then(function (res) {
      if (!res || res.ok === false || !res.ref) throw new Error('rejected');
      ref = String(res.ref);
      upload = String(res.uploadToken || '');
      return uploadPhotos(ref, upload);
    }).then(function (n) {
      say('Finishing up.');
      return request('POST', API + '/api/lead/' + encodeURIComponent(ref) + '/complete', '', { 'Authorization': 'Bearer ' + upload }).then(function () { return n; });
    }).then(function (n) {
      say('');
      photoList.hidden = true;
      busy(false);
      finish(ref, n);
    }, function () {
      say('');
      photoList.hidden = true;
      busy(false);
      failed.hidden = false;
      failed.focus();
    });
  }
  function beacon(p) {
    if (!API || !('sendBeacon' in navigator)) return;
    try { navigator.sendBeacon(API + '/api/lead/beacon', new URLSearchParams(p).toString()); } catch (e) {}
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    fallback.hidden = true;
    failed.hidden = true;
    var bad = fields.filter(problem);
    fields.forEach(function (el) { mark(el, problem(el)); });
    if (bad.length) {
      error.textContent = '';
      bad[0].focus();
      setTimeout(function () {
        error.textContent = sayMissing(bad);
        error.scrollIntoView({ block: 'nearest', behavior: 'instant' });
        bad[0].scrollIntoView({ block: 'nearest', behavior: 'instant' });
      }, 60);
      return;
    }
    error.textContent = '';
    var p = payload();
    setMail(textMessage());
    if (mode === 'send') return send(p);
    beacon(p);
    var left = false;
    var onLeave = function () { left = true; };
    document.addEventListener('visibilitychange', onLeave, { once: true });
    window.addEventListener('pagehide', onLeave, { once: true });
    window.location.href = 'sms:' + PHONE + '?&body=' + encodeURIComponent(textMessage());
    setTimeout(function () {
      document.removeEventListener('visibilitychange', onLeave);
      window.removeEventListener('pagehide', onLeave);
      if (!left && document.visibilityState === 'visible') fallback.hidden = false;
    }, 1500);
  });

  setMode(API && !canText ? 'send' : 'text');
})();

/* Phones: the bottom action bar stays out of the way while the hero buttons or the estimate form are on screen. */
(function () {
  if (!('IntersectionObserver' in window)) { document.documentElement.classList.add('bar-always'); return; }
  var watch = [document.querySelector('.hero-actions'), document.getElementById('estimate')].filter(Boolean);
  if (!watch.length) return;   /* a page with neither (the privacy page) keeps the bar in view */
  var state = watch.map(function () { return false; });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) { state[watch.indexOf(en.target)] = en.isIntersecting; });
    document.body.classList.toggle('bar-away', state.some(Boolean));
  }, { rootMargin: '-66px 0px -64px 0px' });
  document.body.classList.add('bar-away');
  watch.forEach(function (el) { io.observe(el); });
})();

/* Click, tap or press Enter on a photo to see it full size. Adapted from the Byler Cove Anne site. */
(function () {
  try {
    var SEL = '.work-gallery img, .photo-walk img, .hero-photo img';
    var INERT = ['.skip-link', '.site-header', 'main', '.site-footer', '.mobile-actions'];
    var box, inner, pic, cap, prev, next, list = [], at = 0, tx = 0, ty = 0, one = false, ys = 0, opener = null;

    function ok(m) { return !(m.complete && !m.naturalWidth); }
    function pool(m) {
      var g = m.closest('.work-gallery, .photo-walk, .hero-photo') || document;
      list = Array.prototype.slice.call(g.querySelectorAll('img')).filter(ok);
    }
    function big(m) { return m.getAttribute('data-full') || m.currentSrc || m.src; }
    function say(m) {
      var f = m.closest('figure'), c = f ? f.querySelector('figcaption') : null;
      return ((c ? c.textContent : '') || m.getAttribute('alt') || '').trim();
    }
    function setInert(on) {
      INERT.forEach(function (s) {
        var el = document.querySelector(s);
        if (!el) return;
        if (on) el.setAttribute('inert', ''); else el.removeAttribute('inert');
      });
    }
    function lock() {
      ys = window.pageYOffset || document.documentElement.scrollTop || 0;
      var b = document.body.style;
      b.position = 'fixed'; b.top = (-ys) + 'px'; b.left = '0'; b.right = '0'; b.width = '100%';
    }
    function unlock() {
      var b = document.body.style, h = document.documentElement.style;
      b.position = ''; b.top = ''; b.left = ''; b.right = ''; b.width = '';
      h.scrollBehavior = 'auto';
      window.scrollTo(0, ys);
      h.scrollBehavior = '';
    }
    function show(n) {
      if (!list.length) return;
      at = (n + list.length) % list.length;
      var m = list[at], want = big(m), now = m.currentSrc || m.src, t = say(m);
      pic.alt = m.getAttribute('alt') || '';
      cap.textContent = t;
      box.querySelector('.lb-say').textContent = t;
      cap.style.display = t ? '' : 'none';
      prev.style.display = next.style.display = list.length > 1 ? '' : 'none';
      if (pic.getAttribute('src') !== want) {
        pic.onload = function () { inner.style.visibility = ''; box.classList.remove('loading'); };
        pic.onerror = function () { pic.onerror = null; inner.style.visibility = ''; box.classList.remove('loading'); pic.src = now; };
        pic.src = want;
        if (!pic.complete) { inner.style.visibility = 'hidden'; box.classList.add('loading'); }
      }
    }
    function shut() {
      box.classList.remove('on');
      box.setAttribute('aria-hidden', 'true');
      setInert(false);
      unlock();
      pic.onload = pic.onerror = null;
      inner.style.visibility = '';
      box.classList.remove('loading');
      pic.removeAttribute('src');
      if (opener) opener.focus({ preventScroll: true });
    }
    function make() {
      box = document.createElement('div');
      box.className = 'lb';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      box.setAttribute('aria-label', 'Photo viewer');
      box.setAttribute('aria-hidden', 'true');
      box.innerHTML = '<div class="lb-inner"><img class="lb-pic" alt=""><div class="lb-cap" aria-hidden="true"></div></div><p class="lb-say sr-only" aria-live="polite"></p>'
        + '<button type="button" class="lb-x" aria-label="Close">&times;</button>'
        + '<button type="button" class="lb-nav lb-prev" aria-label="Previous photo">&#8249;</button>'
        + '<button type="button" class="lb-nav lb-next" aria-label="Next photo">&#8250;</button>';
      document.body.appendChild(box);
      inner = box.querySelector('.lb-inner');
      pic = box.querySelector('.lb-pic');
      cap = box.querySelector('.lb-cap');
      prev = box.querySelector('.lb-prev');
      next = box.querySelector('.lb-next');
      box.addEventListener('click', function (e) {
        if (e.target.closest('.lb-prev')) return show(at - 1);
        if (e.target.closest('.lb-next')) return show(at + 1);
        if (e.target === pic) return;
        shut();
      });
      box.addEventListener('touchstart', function (e) {
        one = e.touches.length === 1;
        if (one) { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }
      }, { passive: true });
      box.addEventListener('touchmove', function (e) { if (e.touches.length > 1) one = false; }, { passive: true });
      box.addEventListener('touchend', function (e) {
        if (!one) return;
        one = false;
        var vv = window.visualViewport;
        if (vv && vv.scale > 1.05) return;
        var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
        if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)) show(at + (dx < 0 ? 1 : -1));
        else if (Math.abs(dy) > 70 && Math.abs(dy) > Math.abs(dx)) shut();
      }, { passive: true });
    }
    function open(m) {
      if (!box) make();
      pool(m);
      var n = list.indexOf(m);
      if (n < 0) { list = [m]; n = 0; }
      opener = m;
      lock();
      box.classList.add('on');
      box.setAttribute('aria-hidden', 'false');
      show(n);
      setInert(true);
      box.querySelector('.lb-x').focus({ preventScroll: true });
    }
    Array.prototype.slice.call(document.querySelectorAll(SEL)).forEach(function (m) {
      m.setAttribute('tabindex', '0');
      m.setAttribute('role', 'button');
      m.setAttribute('aria-describedby', 'photo-hint');
      m.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(m); }
      });
    });
    document.addEventListener('click', function (e) {
      if (e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var t = e.target;
      if (!t || !t.closest || t.closest('.lb')) return;
      if (t.tagName !== 'IMG' || !t.matches(SEL) || !ok(t)) return;
      e.preventDefault();
      open(t);
    });
    document.addEventListener('keydown', function (e) {
      if (!box || !box.classList.contains('on')) return;
      if (e.key === 'Escape') shut();
      else if (e.key === 'ArrowRight') show(at + 1);
      else if (e.key === 'ArrowLeft') show(at - 1);
      else if (e.key === 'Tab') {
        var f = Array.prototype.slice.call(box.querySelectorAll('button')).filter(function (b) { return getComputedStyle(b).display !== 'none'; });
        var i = f.indexOf(document.activeElement);
        e.preventDefault();
        f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    });
  } catch (err) {}
})();
