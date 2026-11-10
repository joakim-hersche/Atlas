const fs=require('fs'); const {chromium}=require('playwright');
const [,, inPath, kanton, outPng, title]=process.argv;
const d=JSON.parse(fs.readFileSync(inPath)); const topo=JSON.parse(fs.readFileSync(kanton));
// bounds of Switzerland approx
const W=1400,H=920, lon0=5.95, lon1=10.5, lat0=45.8, lat1=47.85;
const kx=W/(lon1-lon0), ky=H/(lat1-lat0)*1.0;
const sx=x=>((x-lon0)*kx).toFixed(1), sy=y=>((lat1-y)*ky).toFixed(1);
function col(t){const c=[[0,'#1a9850'],[30,'#91cf60'],[60,'#fee08b'],[90,'#fc8d59'],[120,'#d73027'],[180,'#7f0000']];for(let i=1;i<c.length;i++){if(t<=c[i][0])return c[i-1][1];}return '#7f0000';}
let segs=d.segments.map(s=>{const p=s[3];let pts=[];for(let i=0;i<p.length;i+=2)pts.push(sx(p[i])+','+sy(p[i+1]));
  return `<polyline points="${pts.join(' ')}" stroke="${col(s[1])}" stroke-width="${s[2]==1?1.6:0.8}" fill="none" opacity="${s[2]==1?0.95:0.6}"/>`}).join('');
// canton outlines from topojson (decode arcs)
const tf=topo.transform, arcs=topo.arcs.map(a=>{let x=0,y=0;return a.map(([dx,dy])=>{x+=dx;y+=dy;return tf?[x*tf.scale[0]+tf.translate[0],y*tf.scale[1]+tf.translate[1]]:[dx,dy]})});
const lines=arcs.map(a=>`<polyline points="${a.map(p=>sx(p[0])+','+sy(p[1])).join(' ')}" stroke="#999" stroke-width="0.8" fill="none"/>`).join('');
const legend=[[30,'≤30'],[60,'≤60'],[90,'≤90'],[120,'≤120'],[180,'≤180'],[999,'>180']].map(([t,l],i)=>`<rect x="${20+i*90}" y="${H-40}" width="18" height="12" fill="${col(t-1)}"/><text x="${42+i*90}" y="${H-30}" font-size="14">${l} min</text>`).join('');
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" style="background:#fff;font-family:sans-serif">${lines}${segs}<text x="20" y="30" font-size="22">${title}</text><text x="20" y="54" font-size="14" fill="#555">${d.segments.length} segments · service day ${d.service_date||''} · departure ${d.departure||''}</text>${legend}</svg>`;
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:W,height:H}});await pg.setContent(svg);await pg.screenshot({path:outPng});await b.close();})();
