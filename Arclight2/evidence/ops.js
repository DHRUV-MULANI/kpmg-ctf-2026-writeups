// Arclight internal console - GraphQL operations reference
// endpoint:  POST /graphql   (Content-Type: application/json)   body: {"query":"..."}
//
// operations this console uses:
//   query    { me { username role } }
//   query    { staff(id: Int) { id username team } }
//   query    { delegation(id: Int) { id owner tier token } }      // owner-only
//   mutation { createAccessRequest(tier: String) { id requester tier status } }
//   mutation { approveRequest(id: Int, sponsor: String) { id status } }
//   query    { rootVault }                                        // root tier only
//
// access flow: file a request, then it has to be approved against a privileged delegation.
async function op(q) {
  const r = await fetch('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: q })
  });
  return r.json();
}
op('{ me { username role } }').then(d => {
  const e = document.getElementById('who');
  if (e) e.textContent = JSON.stringify(d && d.data && d.data.me);
});
