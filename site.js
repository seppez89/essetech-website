// Vercel Web Analytics for this static site. No cookies and no personal data.
// Linked from the <head> of every public page.
(function () {
  window.va = window.va || function () {
    (window.vaq = window.vaq || []).push(arguments);
  };

  var script = document.createElement('script');
  script.defer = true;
  script.src = '/_vercel/insights/script.js';
  document.head.appendChild(script);

  // The free Hobby plan has no custom events, so clicks on phone and email links
  // are counted as page views. They appear under Pages as /clicks/phone and /clicks/email.
  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!link) return;
    var path = link.protocol === 'tel:' ? '/clicks/phone' : '/clicks/email';
    window.va('pageview', { route: path, path: path });
  });
})();
