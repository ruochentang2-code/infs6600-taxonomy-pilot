"use strict";
(() => {
const data = window.CS44_DATA;
const $ = id => document.getElementById(id);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
if (!data || !data.units) { $("metrics").innerHTML='<p class="empty">The saved dataset could not be loaded. Reload this page.</p>'; return; }
const order=["work_integrated_applied","project_problem_based","case_based","entrepreneurial_learning","community_learning","hybrid_learning","simulation","technology_mediated_learning"];
const names={work_integrated_applied:"Work-integrated & applied",project_problem_based:"Project & problem-based",case_based:"Case-based",entrepreneurial_learning:"Entrepreneurial",community_learning:"Community",hybrid_learning:"Hybrid",simulation:"Simulation",technology_mediated_learning:"Technology-mediated"};
const state={level:"ALL",measure:"count",category:"ALL",search:"",selected:"INFS6600"};
const cat = (unit, code) => unit.categories.find(c => c.code===code);
const positiveCount = unit => unit.categories.filter(c=>c.positive===true).length;
const percent = (n,d) => d ? (100*n/d).toFixed(1) : "0.0";
const formatScore = n => Number(n).toFixed(1);
const levelUnits = () => data.units.filter(u => state.level==="ALL" || u.level===state.level);
const filtered = () => levelUnits().filter(u => (state.category==="ALL" || cat(u,state.category)?.positive===true) && (u.code+" "+u.title).toLowerCase().includes(state.search.toLowerCase().trim()));
const categoryDefinition = code => data.categories.find(c=>c.code===code)?.definition || "";
for (const code of order) { const o=document.createElement("option"); o.value=code; o.textContent=names[code]; $("category").appendChild(o); }
function renderMetrics() {
 const units=levelUnits(), evaluated=units.filter(u=>u.status==="selected"), missing=units.length-evaluated.length;
 const rows=[
 ["Units in scope",units.length,state.level==="ALL"?"12 undergraduate · 15 postgraduate":state.level==="UG"?"Undergraduate BIS units":"Postgraduate BIS units",""],
 ["Units analysed",evaluated.length,percent(evaluated.length,units.length)+"% outline coverage","accent"],
 ["Missing outlines",missing,missing?"INFS3080 · 2026 unavailable":"All scoped outlines available",missing?"warning":""],
 ["Teaching categories",data.categories.length,"Multiple categories per unit",""]
 ];
 $("metrics").innerHTML=rows.map(([label,value,sub,style])=>'<article class="metric '+style+'"><div class="metric-label">'+label+'</div><div class="metric-value">'+value+'</div><div class="metric-sub">'+sub+'</div></article>').join("");
 $("filter-context").textContent=(state.level==="ALL"?"Full BIS scope":state.level==="UG"?"Undergraduate scope":"Postgraduate scope")+" · 2026";
}
function renderDistribution() {
 const evaluated=levelUnits().filter(u=>u.status==="selected");
 const denom=evaluated.length;
 const rows=order.map(code=>({code,n:evaluated.filter(u=>cat(u,code)?.positive).length}));
 const max=state.measure==="rate"?100:Math.max(...rows.map(r=>r.n),1);
 $("chart-cohort").textContent=denom+" evaluated "+(state.level==="ALL"?"units":state.level+" units");
 $("distribution").innerHTML=rows.map(r=>{
  const rate=100*r.n/(denom||1),width=100*(state.measure==="rate"?rate:r.n)/max;
  const aria=names[r.code]+": "+r.n+" of "+denom+" units ("+percent(r.n,denom)+" percent). Filter units.";
  return '<button class="bar-row '+(r.n===0?"zero ":"")+(state.category===r.code?"selected":"")+'" data-category="'+r.code+'" aria-pressed="'+(state.category===r.code)+'" aria-label="'+esc(aria)+'" title="'+esc(categoryDefinition(r.code))+'"><span class="bar-name">'+names[r.code]+'</span><span class="bar-track" aria-hidden="true"><span class="bar-fill" style="display:block;width:'+width+'%"></span></span><span class="bar-number">'+(state.measure==="rate"?percent(r.n,denom)+"%":r.n)+'</span></button>';
 }).join("");
}
function renderComparison() {
 $("comparison").innerHTML=order.map(code=>'<div class="compare-row"><span class="compare-name">'+names[code]+'</span><div class="compare-bars">'+["UG","PG"].map(level=>{
  const r=data.aggregate.find(r=>r.level===level && r.category_code===code),pct=Number(r.positive_pct_evaluated),n=+r.positive_courses;
  return '<div class="compare-line" aria-label="'+esc(level+" "+names[code]+": "+n+" of "+r.evaluated_courses+", "+pct+" percent")+'" title="'+level+': '+n+' / '+r.evaluated_courses+'"><span class="compare-track" aria-hidden="true"><span class="compare-fill '+(level==="PG"?"pg":"")+'" style="display:block;width:'+pct+'%"></span></span><span class="compare-value">'+pct.toFixed(1)+'%</span></div>';
 }).join("")+'</div></div>').join("");
}
function renderUnits() {
 const units=filtered();
 if (!units.some(u=>u.code===state.selected)) state.selected=units[0]?.code || null;
 $("unit-count").textContent=units.length+" of "+levelUnits().length+" units";
 $("filter-note").hidden=state.category==="ALL";
 $("filter-note").textContent=state.category==="ALL"?"":"Showing units with positive "+names[state.category].toLowerCase()+" evidence. Overview totals remain based on the selected study level.";
 $("units").innerHTML=units.map(u=>'<tr class="'+(u.code===state.selected?"selected":"")+'"><td><button class="unit-link" data-unit="'+u.code+'" aria-label="View '+u.code+' '+esc(u.title)+'" aria-pressed="'+(u.code===state.selected)+'">'+u.code+'</button><span class="unit-name">'+esc(u.title)+'</span></td><td><span class="level-badge '+(u.level==="PG"?"pg":"")+'">'+u.level+'</span></td><td class="count-cell">'+(u.status==="selected"?positiveCount(u):"—")+'</td><td><span class="coverage '+(u.status==="selected"?"available":"missing")+'">'+(u.status==="selected"?"Available":"Missing")+'</span></td></tr>').join("");
 $("empty").hidden=!!units.length;
 document.querySelector(".unit-table").hidden=!units.length;
 renderDetail();
}
function renderDetail() {
 const u=data.units.find(u=>u.code===state.selected);
 if(!u){$("unit-detail").innerHTML='<div class="empty"><strong>No unit selected</strong><p>Change the filters to explore unit results.</p></div>';return;}
 let html='<div class="detail-kicker"><span>UNIT PROFILE</span><span>'+esc(u.level==="UG"?"UNDERGRADUATE":"POSTGRADUATE")+'</span></div><h3 class="detail-code">'+u.code+'</h3><p class="detail-title">'+esc(u.title)+'</p>';
 if(u.status!=="selected"){
  html+='<span class="pill preliminary">Outline unavailable</span><div class="missing-box"><strong>No eligible 2026 outline</strong><p>INFS3080 is retained in the scope but excluded from the evaluated denominator. The proposed 2025 fallback has not been imported into this snapshot.</p></div><p class="detail-note">Classification results are unavailable. Missing data must not be read as zero evidence.</p>';
 } else {
  const reviewTotal=u.categories.reduce((n,c)=>n+c.review,0);
  html+='<div class="detail-meta"><span class="level-badge '+(u.level==="PG"?"pg":"")+'">'+u.level+'</span><span>2026 · '+esc(u.session)+'</span><span>·</span><span>Automated classification</span></div>';
  html+='<div class="detail-stats"><div class="detail-stat"><strong>'+positiveCount(u)+' <span>/ 8</span></strong><span>Positive categories</span></div><div class="detail-stat"><strong>'+reviewTotal+'</strong><span>Review item–category records</span></div></div>';
  html+='<table class="results-table"><thead><tr><th scope="col">CATEGORY / RESULT</th><th scope="col">POSITIVE<br>ITEMS</th><th scope="col">POSITIVE<br>SCORE</th><th scope="col">REVIEW<br>ITEMS</th></tr></thead><tbody>';
  html+=order.map(code=>{const c=cat(u,code),status=c.positive?"Positive":c.review>0?"Review only":"No match";return '<tr class="'+(state.category===code?"highlighted":"")+'" title="'+esc(categoryDefinition(code))+'"><td><span class="result-category">'+names[code]+'</span><span class="result-status '+(c.positive?"positive":c.review>0?"review":"")+'">'+status+'</span></td><td>'+c.items+'</td><td class="score-cell">'+formatScore(c.score)+'</td><td class="'+(c.review>0?"review-number":"")+'">'+c.review+'</td></tr>';}).join("");
  html+='</tbody></table><p class="detail-note">Positive scores exclude review results. The same item may appear in multiple categories. Human validation is pending.</p><a class="outline-link" href="'+esc(u.url)+'" target="_blank" rel="noopener noreferrer">Open original unit outline <span aria-hidden="true">↗</span></a><p class="detail-note" style="margin-bottom:0">The live outline may have changed since the saved capture.</p>';
 }
 $("unit-detail").innerHTML=html;
}
function render(){renderMetrics();renderDistribution();renderUnits();}
function reset(){state.level="ALL";state.category="ALL";state.search="";state.selected="INFS6600";$("search").value="";$("category").value="ALL";document.querySelectorAll("[data-level]").forEach(b=>b.setAttribute("aria-pressed",b.dataset.level==="ALL"));render();}
document.querySelectorAll("[data-level]").forEach(b=>b.addEventListener("click",()=>{state.level=b.dataset.level;document.querySelectorAll("[data-level]").forEach(x=>x.setAttribute("aria-pressed",x===b));render();}));
document.querySelectorAll("[data-measure]").forEach(b=>b.addEventListener("click",()=>{state.measure=b.dataset.measure;document.querySelectorAll("[data-measure]").forEach(x=>x.setAttribute("aria-pressed",x===b));renderDistribution();}));
$("distribution").addEventListener("click",e=>{const b=e.target.closest("[data-category]");if(!b)return;state.category=state.category===b.dataset.category?"ALL":b.dataset.category;$("category").value=state.category;renderDistribution();renderUnits();});
$("category").addEventListener("change",e=>{state.category=e.target.value;renderDistribution();renderUnits();});
$("search").addEventListener("input",e=>{state.search=e.target.value;renderUnits();});
$("units").addEventListener("click",e=>{const b=e.target.closest("[data-unit]");if(!b)return;state.selected=b.dataset.unit;renderUnits();});
$("reset").addEventListener("click",reset);$("empty-reset").addEventListener("click",reset);
document.querySelectorAll(".nav-link").forEach(a=>a.addEventListener("click",()=>{document.querySelectorAll(".nav-link").forEach(x=>x.classList.toggle("active",x===a));if(a.hash==="#method")document.querySelector("#method details").open=true;}));
render();renderComparison();
})();
