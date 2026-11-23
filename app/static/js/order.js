/* Menu and Orders screen: search, category filter and the "Current order" cart. */
(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll('tr.dish'));
  var cart = {};            // menu item id -> {name, price, qty}
  var order = [];           // keeps the order in which dishes were added
  var body = document.getElementById('cart-body');
  var fields = document.getElementById('cart-fields');
  var subtotalEl = document.getElementById('subtotal');
  var submitBtn = document.getElementById('submit-order');
  var activeCat = '';

  function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
  function norm(s) {
    return (s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  function el(tag, text, attrs) {
    var e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    for (var k in (attrs || {})) e.setAttribute(k, attrs[k]);
    return e;
  }

  function render() {
    body.innerHTML = '';
    fields.innerHTML = '';
    var total = 0;
    if (!order.length) {
      var tr = el('tr', undefined, { 'class': 'empty' });
      var td = el('td', 'No dishes selected.', { colspan: 4 });
      tr.appendChild(td); body.appendChild(tr);
    }
    order.forEach(function (id) {
      var it = cart[id], line = it.qty * it.price;
      total += line;
      var tr = el('tr');
      tr.appendChild(el('td', it.name));
      var q = el('td', undefined, { 'class': 'qtycell' });
      q.appendChild(el('button', '-', { type: 'button', 'data-act': 'dec', 'data-id': id }));
      q.appendChild(document.createTextNode(' ' + it.qty + ' '));
      q.appendChild(el('button', '+', { type: 'button', 'data-act': 'inc', 'data-id': id }));
      tr.appendChild(q);
      tr.appendChild(el('td', fmt(line), { 'class': 'num' }));
      var x = el('td'); x.appendChild(el('button', '[x]', { type: 'button', 'class': 'linkbtn', 'data-act': 'del', 'data-id': id }));
      tr.appendChild(x);
      body.appendChild(tr);
      fields.appendChild(el('input', undefined, { type: 'hidden', name: 'qty_' + id, value: it.qty }));
    });
    subtotalEl.textContent = fmt(total) + ' VND';
    submitBtn.disabled = !order.length;
  }

  function add(id, name, price) {
    if (!cart[id]) { cart[id] = { name: name, price: price, qty: 0 }; order.push(id); }
    if (cart[id].qty < 50) cart[id].qty += 1;
    render();
  }
  function remove(id) { delete cart[id]; order = order.filter(function (x) { return x !== id; }); }

  body.addEventListener('click', function (e) {
    var act = e.target.getAttribute('data-act'), id = e.target.getAttribute('data-id');
    if (!act) return;
    if (act === 'inc' && cart[id].qty < 50) cart[id].qty += 1;
    if (act === 'dec') { cart[id].qty -= 1; if (cart[id].qty < 1) remove(id); }
    if (act === 'del') remove(id);
    render();
  });

  rows.forEach(function (row) {
    var btn = row.querySelector('.add');
    if (btn) btn.addEventListener('click', function () {
      add(row.dataset.id, row.dataset.name, +row.dataset.price);
    });
  });

  function applyFilter() {
    var key = norm(document.getElementById('search').value), shown = 0;
    rows.forEach(function (row) {
      var ok = (!activeCat || row.dataset.cat === activeCat) && (!key || row.dataset.search.indexOf(key) !== -1);
      row.classList.toggle('hidden', !ok);
      if (ok) shown += 1;
    });
    document.getElementById('nomatch').hidden = shown !== 0;
  }
  document.getElementById('search').addEventListener('input', applyFilter);
  document.getElementById('search-btn').addEventListener('click', applyFilter);
  document.getElementById('chips').addEventListener('click', function (e) {
    if (!e.target.classList.contains('chip')) return;
    Array.prototype.forEach.call(document.querySelectorAll('#chips .chip'), function (c) { c.classList.remove('on'); });
    e.target.classList.add('on');
    activeCat = e.target.dataset.cat;
    applyFilter();
  });
  document.getElementById('clear-cart').addEventListener('click', function () { cart = {}; order = []; render(); });

  // Avoid sending the form twice by double click
  document.getElementById('order-form').addEventListener('submit', function () { submitBtn.disabled = true; });
  render();
})();
