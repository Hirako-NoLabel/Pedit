const $ = (s) => document.querySelector(s);
const state = {
  id:null,name:null,outputName:null,pageCount:0,currentPage:0,pageData:null,
  scale:1.7,zoom:1,viewMode:'fit-width',edits:new Map(),undo:[],redo:[],selected:null,
  previewUrl:null,renderToken:0,previewTimer:null,cleanPreview:false,
  feasibility:new Map(),feasibilityToken:0,selectionMode:'smart',cycleSig:'',cycleIndex:0,
  batchMatches:[],batchSource:null,batchBusy:false,runBusy:false,changeLogExport:false,pageNumberMatches:[],pageNumberScanResults:[],pageNumberTemplates:{A:null,B:null},pageNumberBusy:false,pageNumberBoxSlot:null,pageNumberBoxRect:null,pageNumberBoxSelecting:false,pageNumberBoxTarget:null,pageNumberPageOverrides:{},pageNumberBatchSeq:0,lastPageNumberBatch:null,pageProgressActive:false,scanTuneClipboard:null,glyphClipboard:null,glyphLibrary:new Map(),pendingReusableGlyph:null,blockClipboard:null,blockLibrary:new Map(),deleteMatches:[],deleteBusy:false,
  documentType:'unknown',diagnosis:null,ocrAvailable:false,ocrReason:'',ocrLang:'',ocrBackend:'',ocrBackendLabel:'',manualSelectionRect:null,manualSelecting:false,suppressNextClick:false,snapEnabled:true,transformDrag:null,objectLayerOpen:false,objectLayerAll:false,detailZoom:4,detailCrop:null,pageNumberAnomalyOnly:false,pageNumberManualTakeovers:new Set(),
  versionHistory:[],versionSeq:0,historySelectedId:null,pendingHistoryLabel:null,pendingHistoryMeta:null,changeLogSelectedKeys:new Set()
};

const els = {
  importBtn:$('#importBtn'),welcomeImport:$('#welcomeImport'),fileInput:$('#fileInput'),exportBtn:$('#exportBtn'),changeLogBtn:$('#revisionRecordsBtn'),pageNumberBtn:$('#pageNumberBtn'),
  undoBtn:$('#undoBtn'),redoBtn:$('#redoBtn'),historyBtn:$('#revisionRecordsBtn'),pagesPanel:$('#pagesPanel'),propertiesPanel:$('#propertiesPanel'),
  welcome:$('#welcome'),viewer:$('#viewer'),thumbList:$('#thumbList'),pageCountBadge:$('#pageCountBadge'),
  pageImage:$('#pageImage'),pageWrap:$('#pageWrap'),overlayLayer:$('#overlayLayer'),loadingMask:$('#loadingMask'),loadingTitle:$('#loadingTitle'),loadingPercent:$('#loadingPercent'),loadingProgressBar:$('#loadingProgressBar'),
  currentPageLabel:$('#currentPageLabel'),totalPagesLabel:$('#totalPagesLabel'),prevPage:$('#prevPage'),nextPage:$('#nextPage'),
  zoomOut:$('#zoomOut'),zoomIn:$('#zoomIn'),fitWidth:$('#fitWidth'),fitPage:$('#fitPage'),editLine:$('#editLine'),cleanPreview:$('#cleanPreview'),zoomLabel:$('#zoomLabel'),pageScroll:$('#pageScroll'),selectionMode:$('#selectionMode'),snapToggle:$('#snapToggle'),objectLayerToggle:$('#objectLayerToggle'),
  objectType:$('#objectType'),emptyProps:$('#emptyProps'),textProps:$('#textProps'),imageProps:$('#imageProps'),
  textContent:$('#textContent'),finalGlyphPreviewCard:$('#finalGlyphPreviewCard'),finalGlyphPreviewText:$('#finalGlyphPreviewText'),finalGlyphPreviewMode:$('#finalGlyphPreviewMode'),finalGlyphPreviewHint:$('#finalGlyphPreviewHint'),fontSize:$('#fontSize'),fontColor:$('#fontColor'),fontName:$('#fontName'),textX:$('#textX'),textY:$('#textY'),
  resetTextBtn:$('#resetTextBtn'),precisionMode:$('#precisionMode'),batchApplyBtn:$('#batchApplyBtn'),imageInput:$('#imageInput'),imageFit:$('#imageFit'),replacementPreview:$('#replacementPreview'),imagePlaceholder:$('#imagePlaceholder'),resetImageBtn:$('#resetImageBtn'),
  fileNameLabel:$('#fileNameLabel'),changeCount:$('#changeCount'),toast:$('#toast'),
  batchModal:$('#batchModal'),batchClose:$('#batchClose'),batchFieldSummary:$('#batchFieldSummary'),batchSamePosition:$('#batchSamePosition'),batchSelectAll:$('#batchSelectAll'),batchSelectNone:$('#batchSelectNone'),batchInvert:$('#batchInvert'),batchRange:$('#batchRange'),batchRangeApply:$('#batchRangeApply'),batchScanStatus:$('#batchScanStatus'),batchPageGrid:$('#batchPageGrid'),batchResult:$('#batchResult'),batchRescan:$('#batchRescan'),batchTrial:$('#batchTrial'),batchConfirm:$('#batchConfirm'),
  topFileName:$('#topFileName'),documentPill:$('#documentPill'),dropZone:$('#dropZone'),statusPageMirror:$('#statusPageMirror'),statusZoomMirror:$('#statusZoomMirror'),
  engineStatusText:$('#engineStatusText'),documentModeHint:$('#documentModeHint'),emptyPropsText:$('#emptyPropsText'),emptyPropsTip:$('#emptyPropsTip'),
  runEditBtn:$('#runEditBtn'),runEditLabel:$('#runEditLabel'),runProcess:$('#runProcess'),runStatusTitle:$('#runStatusTitle'),runProgressText:$('#runProgressText'),runProgressBar:$('#runProgressBar'),runSteps:$('#runSteps'),runMessage:$('#runMessage'),
  changeLogModal:$('#changeLogModal'),changeLogClose:$('#changeLogClose'),changeLogCancel:$('#changeLogCancel'),changeLogConfirm:$('#changeLogConfirm'),changeLogSummary:$('#changeLogSummary'),changeLogList:$('#changeLogList'),changeLogUndoSelected:$('#changeLogUndoSelected'),changeLogRestoreBeforeSelected:$('#changeLogRestoreBeforeSelected'),
  compareSection:$('#compareSection'),compareImage:$('#compareImage'),compareNote:$('#compareNote')
  ,scanFieldInfo:$('#scanFieldInfo'),ocrOriginal:$('#ocrOriginal'),currentOcrField:$('#currentOcrField'),replaceLabel:$('#replaceLabel'),
  scanTuneSection:$('#scanTuneSection'),scanTuneCopy:$('#scanTuneCopy'),scanTunePaste:$('#scanTunePaste'),applyScanTune:$('#applyScanTune'),scanFontChoice:$('#scanFontChoice'),copyFinishedGlyph:$('#copyFinishedGlyph'),pasteFinishedGlyph:$('#pasteFinishedGlyph'),finishedGlyphMode:$('#finishedGlyphMode'),finishedGlyphLibrary:$('#finishedGlyphLibrary'),
  scanSizeScale:$('#scanSizeScale'),scanSizeValue:$('#scanSizeValue'),scanSizeInput:$('#scanSizeInput'),scanWidthScale:$('#scanWidthScale'),scanWidthValue:$('#scanWidthValue'),scanWidthInput:$('#scanWidthInput'),
  scanXOffset:$('#scanXOffset'),scanXValue:$('#scanXValue'),scanXInput:$('#scanXInput'),scanYOffset:$('#scanYOffset'),scanYValue:$('#scanYValue'),scanYInput:$('#scanYInput'),
  scanDarkness:$('#scanDarkness'),scanDarknessValue:$('#scanDarknessValue'),scanDarknessInput:$('#scanDarknessInput'),scanStroke:$('#scanStroke'),scanStrokeValue:$('#scanStrokeValue'),scanStrokeInput:$('#scanStrokeInput'),
  scanClarity:$('#scanClarity'),scanClarityValue:$('#scanClarityValue'),scanClarityInput:$('#scanClarityInput'),scanTuneSummary:$('#scanTuneSummary'),scanCleanup:$('#scanCleanup'),scanCleanupValue:$('#scanCleanupValue'),scanCleanupInput:$('#scanCleanupInput'),
  scanEdgeBlend:$('#scanEdgeBlend'),scanEdgeBlendValue:$('#scanEdgeBlendValue'),scanEdgeBlendInput:$('#scanEdgeBlendInput'),
  manualGeometrySection:$('#manualGeometrySection'),blockX:$('#blockX'),blockY:$('#blockY'),blockW:$('#blockW'),blockH:$('#blockH'),objectLockBtn:$('#objectLockBtn'),reRecognizeBlock:$('#reRecognizeBlock'),convertFreeText:$('#convertFreeText'),openDetailEditor:$('#openDetailEditor'),resetBlockPosition:$('#resetBlockPosition'),saveFinishedBlock:$('#saveFinishedBlock'),pasteFinishedBlock:$('#pasteFinishedBlock'),finishedBlockLibrary:$('#finishedBlockLibrary'),
  objectLayerPanel:$('#objectLayerPanel'),objectLayerClose:$('#objectLayerClose'),objectLayerEditedOnly:$('#objectLayerEditedOnly'),objectLayerAll:$('#objectLayerAll'),objectLayerList:$('#objectLayerList'),
  deleteTextBtn:$('#deleteTextBtn'),deleteImageBtn:$('#deleteImageBtn'),deleteModal:$('#deleteModal'),deleteModalClose:$('#deleteModalClose'),deleteCancel:$('#deleteCancel'),deleteModalTitle:$('#deleteModalTitle'),deleteModalSummary:$('#deleteModalSummary'),deleteSourceCard:$('#deleteSourceCard'),deleteCurrentOnly:$('#deleteCurrentOnly'),deleteFindMatches:$('#deleteFindMatches'),deleteRange:$('#deleteRange'),deleteRangeApply:$('#deleteRangeApply'),deleteStatus:$('#deleteStatus'),deleteMatchGrid:$('#deleteMatchGrid'),deleteConfirm:$('#deleteConfirm'),
  pageNumberModal:$('#pageNumberModal'),pageNumberClose:$('#pageNumberClose'),pageNumberFrom:$('#pageNumberFrom'),pageNumberTo:$('#pageNumberTo'),pageNumberStart:$('#pageNumberStart'),pageNumberEnd:$('#pageNumberEnd'),pageNumberScan:$('#pageNumberScan'),pageNumberApply:$('#pageNumberApply'),pageNumberStatus:$('#pageNumberStatus'),pageNumberResults:$('#pageNumberResults'),
  pageNumberUseA:$('#pageNumberUseA'),pageNumberClearA:$('#pageNumberClearA'),pageNumberSlotAState:$('#pageNumberSlotAState'),pageNumberFormatA:$('#pageNumberFormatA'),pageNumberCustomA:$('#pageNumberCustomA'),pageNumberRangeFromA:$('#pageNumberRangeFromA'),pageNumberRangeToA:$('#pageNumberRangeToA'),pageNumberAllowAddA:$('#pageNumberAllowAddA'),
  pageNumberUseB:$('#pageNumberUseB'),pageNumberClearB:$('#pageNumberClearB'),pageNumberSlotBState:$('#pageNumberSlotBState'),pageNumberFormatB:$('#pageNumberFormatB'),pageNumberCustomB:$('#pageNumberCustomB'),pageNumberRangeFromB:$('#pageNumberRangeFromB'),pageNumberRangeToB:$('#pageNumberRangeToB'),pageNumberAllowAddB:$('#pageNumberAllowAddB'),
  pageNumberTotalMode:$('#pageNumberTotalMode'),pageNumberTotalValue:$('#pageNumberTotalValue'),pageNumberPreviewSummary:$('#pageNumberPreviewSummary'),pageNumberSlotGrid:$('#pageNumberSlotGrid'),pageNumberAddSlot:$('#pageNumberAddSlot'),pageNumberTrial:$('#pageNumberTrial'),pageNumberAnomaly:$('#pageNumberAnomaly'),pageNumberUndoBatch:$('#pageNumberUndoBatch'),
  detailEditorModal:$('#detailEditorModal'),detailEditorClose:$('#detailEditorClose'),detailEditorDone:$('#detailEditorDone'),detailStage:$('#detailStage'),detailCanvas:$('#detailCanvas'),detailObject:$('#detailObject'),detailEditorInfo:$('#detailEditorInfo'),
  historyModal:$('#changeLogModal'),historyClose:$('#changeLogClose'),historyCancel:$('#historyCancel'),historyList:$('#historyList'),historySummary:$('#historySummary'),historyRestore:$('#historyRestore'),historyRename:$('#historyRename')
};

function toast(msg,ms=2200){els.toast.textContent=msg;els.toast.classList.remove('hidden');clearTimeout(toast.t);toast.t=setTimeout(()=>els.toast.classList.add('hidden'),ms);}
function showLoading(v){els.loadingMask.classList.toggle('hidden',!v);if(v)setPageLoading('处理中…',8);}
function setPageLoading(title,progress){if(els.loadingTitle)els.loadingTitle.textContent=title||'处理中…';if(els.loadingPercent)els.loadingPercent.textContent=`${Math.round(progress||0)}%`;if(els.loadingProgressBar)els.loadingProgressBar.style.width=`${Math.max(0,Math.min(100,progress||0))}%`;}
function beginPageProgress(title='正在处理…'){state.pageProgressActive=true;showLoading(true);setPageLoading(title,5);}
function endPageProgress(){state.pageProgressActive=false;showLoading(false);}
function editKey(type,page,id){return `${type}:${page}:${id}`;}
function allEdits(){return [...state.edits.values()];}
function snapshot(){return JSON.stringify([...state.edits.entries()]);}
function formatHistoryTime(ts){const d=new Date(ts);return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;}
function captureVersion(label='编辑文档',meta={},force=false){
  if(!state.id)return null;const snap=snapshot(),last=state.versionHistory[state.versionHistory.length-1];if(!force&&last?.snapshot===snap)return last;
  const v={id:++state.versionSeq,time:Date.now(),label:String(label||'编辑文档'),page:meta.page||state.currentPage+1,detail:String(meta.detail||''),snapshot:snap,name:String(meta.name||''),sourceVersionId:meta.sourceVersionId||null,editCount:state.edits.size,baselineId:Number(meta.baselineId??state.currentBaselineId??0)};
  state.versionHistory.push(v);if(state.versionHistory.length>160)state.versionHistory.shift();state.historySelectedId=v.id;renderVersionHistory();return v;
}
function queueVersion(label='编辑文档',meta={}){state.pendingHistoryLabel=label;state.pendingHistoryMeta=meta;}
function restoreSnapshot(s){state.edits=new Map(JSON.parse(s));state.feasibility.clear();state.pageNumberScanResults=[];state.pageNumberMatches=[];if(els.pageNumberResults)els.pageNumberResults.innerHTML='';if(els.pageNumberApply)els.pageNumberApply.disabled=true;updateHistoryButtons();updateChangeCount();renderOverlays();schedulePreview();if(state.selected)showSelectedProps();}
function pushHistory(label='编辑文档',meta={}){state.undo.push(snapshot());if(state.undo.length>80)state.undo.shift();state.redo=[];queueVersion(label,meta);updateHistoryButtons();}
function updateHistoryButtons(){els.undoBtn.disabled=state.undo.length===0;els.redoBtn.disabled=state.redo.length===0;}
function updateChangeCount(){
  const pages=new Set(allEdits().map(e=>e.page));
  els.changeCount.textContent=state.edits.size?`${state.edits.size} 处 · ${pages.size} 页`:'0 处';
  document.querySelectorAll('.thumb').forEach(t=>{const p=+t.dataset.page;let dot=t.querySelector('.edit-dot');const has=allEdits().some(e=>e.page===p);if(has&&!dot){dot=document.createElement('span');dot.className='edit-dot';t.appendChild(dot);}else if(!has&&dot)dot.remove();});
  if(state.pendingHistoryLabel){const label=state.pendingHistoryLabel,meta=state.pendingHistoryMeta||{};state.pendingHistoryLabel=null;state.pendingHistoryMeta=null;captureVersion(label,meta);}
}
async function apiError(resp){try{const j=await resp.json();return j.error||'操作失败';}catch{return `操作失败 (${resp.status})`;}}

function versionById(id){return state.versionHistory.find(v=>v.id===id)||null;}
function renderVersionHistory(){
  if(!els.historyList)return;els.historyList.innerHTML='';const arr=[...state.versionHistory].reverse();
  if(els.historySummary)els.historySummary.textContent=arr.length?`${arr.length} 个历史节点 · 当前 ${state.edits.size} 处修改`:'暂无历史记录';
  if(!arr.length){els.historyList.innerHTML='<div class="history-empty">暂无修改历史。成功运行、批量操作、删除和页码修改后会自动记录。</div>';if(els.historyRestore)els.historyRestore.disabled=true;if(els.historyRename)els.historyRename.disabled=true;return;}
  for(const v of arr){const row=document.createElement('button');row.type='button';const isCurrent=v.snapshot===snapshot();row.className='version-history-item'+(v.id===state.historySelectedId?' selected':'')+(isCurrent?' current':'');row.dataset.versionId=v.id;const title=v.name||v.label;row.innerHTML=`<span class="version-history-dot"></span><span class="version-history-main"><strong>${escapeHtml(title)}</strong><small>${formatHistoryTime(v.time)} · 第 ${v.page} 页 · ${v.editCount} 处修改${v.detail?` · ${escapeHtml(v.detail)}`:''}</small>${v.sourceVersionId?`<em>从历史节点 #${v.sourceVersionId} 恢复后继续</em>`:''}</span><span class="version-history-id">${isCurrent?'当前 · ':''}#${v.id}</span>`;row.onclick=()=>{state.historySelectedId=v.id;renderVersionHistory();};els.historyList.appendChild(row);}
  const selected=versionById(state.historySelectedId);if(els.historyRestore)els.historyRestore.disabled=!selected;if(els.historyRename)els.historyRename.disabled=!selected;
}
function openVersionHistory(){if(!state.id)return;renderVersionHistory();els.historyModal?.classList.remove('hidden');}
function closeVersionHistory(){els.historyModal?.classList.add('hidden');}
async function restoreHistoryVersion(){const v=versionById(state.historySelectedId);if(!v)return;const current=snapshot();if(current===v.snapshot){toast('当前已经是这个历史版本');return;}state.undo.push(current);if(state.undo.length>80)state.undo.shift();state.redo=[];restoreSnapshot(v.snapshot);captureVersion(`返回到历史 #${v.id}`,{page:v.page,detail:v.name||v.label,sourceVersionId:v.id},true);closeVersionHistory();if(state.currentPage!==Math.max(0,(v.page||1)-1))await loadPage(Math.max(0,(v.page||1)-1));else await refreshPreview();toast(`已返回到历史 #${v.id}：${v.name||v.label}`,4200);}
function renameHistoryVersion(){const v=versionById(state.historySelectedId);if(!v)return;const name=prompt('为这个历史节点命名：',v.name||'');if(name===null)return;v.name=name.trim();renderVersionHistory();}

const DEFAULT_SCAN_VISUAL_ADJUST=Object.freeze({fontChoice:'input',sizeScale:1,widthScale:1,xOffsetPx:0,yOffsetPx:0,darkness:0,strokePx:0,clarity:0,softenPx:0,cleanupStrength:50,edgeBlend:0});
const SCAN_TUNE_META=Object.freeze({
  scanSizeScale:{inputId:'scanSizeInput',min:50,max:150,step:.1,digits:1},scanWidthScale:{inputId:'scanWidthInput',min:50,max:150,step:.1,digits:1},
  scanXOffset:{inputId:'scanXInput',min:-600,max:600,step:.1,digits:1},scanYOffset:{inputId:'scanYInput',min:-600,max:600,step:.1,digits:1},
  scanDarkness:{inputId:'scanDarknessInput',min:-100,max:100,step:.1,digits:1},scanStroke:{inputId:'scanStrokeInput',min:-6,max:6,step:.1,digits:1},
  scanClarity:{inputId:'scanClarityInput',min:-100,max:100,step:.1,digits:1},scanCleanup:{inputId:'scanCleanupInput',min:0,max:100,step:.1,digits:1},
  scanEdgeBlend:{inputId:'scanEdgeBlendInput',min:-100,max:100,step:.1,digits:1}
});
function normalizeScanVisualAdjust(v={}){return {...DEFAULT_SCAN_VISUAL_ADJUST,...(v||{})};}
function visualAdjustEqual(a,b){return JSON.stringify(normalizeScanVisualAdjust(a))===JSON.stringify(normalizeScanVisualAdjust(b));}
function tuneNumber(v,digits=1){const n=Number(v);if(!Number.isFinite(n))return '0';return n.toFixed(digits).replace(/\.0$/,'').replace(/(\.\d*[1-9])0+$/,'$1');}
function clampTuneValue(id,value){const meta=SCAN_TUNE_META[id];let n=Number(value);if(!Number.isFinite(n))n=Number(SCAN_TUNE_DEFAULT_BY_ID[id]??0);if(!meta)return n;const step=Number(meta.step)||1;n=Math.max(meta.min,Math.min(meta.max,n));return Math.round(n/step)*step;}
function syncTuneNumberInputs(){for(const [id,meta] of Object.entries(SCAN_TUNE_META)){const input=els[meta.inputId],range=els[id];if(input&&range)input.value=tuneNumber(range.value,meta.digits||1);}}
function readScanVisualAdjust(){
  return normalizeScanVisualAdjust({
    fontChoice:els.scanFontChoice?.value||'input',sizeScale:(Number(els.scanSizeScale.value)||100)/100,widthScale:(Number(els.scanWidthScale.value)||100)/100,
    xOffsetPx:Number(els.scanXOffset.value)||0,yOffsetPx:Number(els.scanYOffset.value)||0,darkness:Number(els.scanDarkness.value)||0,
    strokePx:Number(els.scanStroke.value)||0,clarity:Number(els.scanClarity.value)||0,softenPx:0,cleanupStrength:Number(els.scanCleanup.value),edgeBlend:Number(els.scanEdgeBlend.value)
  });
}
function scanAdjustIsDefault(v){return visualAdjustEqual(v,DEFAULT_SCAN_VISUAL_ADJUST);}
function formatSigned(v,suffix=''){const n=Number(v)||0;return `${n>0?'+':''}${tuneNumber(n,1)}${suffix}`;}
function renderScanTuneValues(){
  if(!els.scanSizeScale)return;
  els.scanSizeValue.textContent=`${tuneNumber(els.scanSizeScale.value,1)}%`;els.scanWidthValue.textContent=`${tuneNumber(els.scanWidthScale.value,1)}%`;
  els.scanXValue.textContent=formatSigned(els.scanXOffset.value,' px');els.scanYValue.textContent=formatSigned(els.scanYOffset.value,' px');
  const d=Number(els.scanDarkness.value)||0;els.scanDarknessValue.textContent=Math.abs(d)>.0001?`${d>0?'更深 ':'更浅 '}${tuneNumber(Math.abs(d),1)}`:'自动';
  const st=Number(els.scanStroke.value)||0;els.scanStrokeValue.textContent=Math.abs(st)>.0001?`${st>0?'加粗 ':'变细 '}${tuneNumber(Math.abs(st),1)}`:'自动';
  const cl=Number(els.scanClarity.value)||0;els.scanClarityValue.textContent=Math.abs(cl)>.0001?`${cl>0?'更清晰 ':'更柔 '}${tuneNumber(Math.abs(cl),1)}`:'自动';
  els.scanCleanupValue.textContent=tuneNumber(els.scanCleanup.value,1);const eb=Number(els.scanEdgeBlend.value)||0;els.scanEdgeBlendValue.textContent=Math.abs(eb)>.0001?`${eb>0?'+':''}${tuneNumber(eb,1)}`:'自动';
  syncTuneNumberInputs();
  if(els.scanTuneSummary){const a=readScanVisualAdjust(),changed=Object.entries(a).filter(([k,v])=>k!=='softenPx'&&JSON.stringify(v)!==JSON.stringify(DEFAULT_SCAN_VISUAL_ADJUST[k])).length;els.scanTuneSummary.textContent=changed?`已调整 ${changed} 项`:'自动 · 未调整';}
}
function loadScanVisualAdjust(v){
  const a=normalizeScanVisualAdjust(v);
  if(els.scanFontChoice)els.scanFontChoice.value=a.fontChoice||'input';els.scanSizeScale.value=tuneNumber(a.sizeScale*100,1);els.scanWidthScale.value=tuneNumber(a.widthScale*100,1);
  els.scanXOffset.value=tuneNumber(a.xOffsetPx,1);els.scanYOffset.value=tuneNumber(a.yOffsetPx,1);els.scanDarkness.value=tuneNumber(a.darkness,1);els.scanStroke.value=tuneNumber(a.strokePx,1);
  els.scanClarity.value=tuneNumber(Number(a.clarity??(-25*(a.softenPx||0))),1);els.scanCleanup.value=tuneNumber(a.cleanupStrength,1);els.scanEdgeBlend.value=tuneNumber(a.edgeBlend,1);renderScanTuneValues();
}

const SCAN_TUNE_DEFAULT_BY_ID=Object.freeze({
  scanFontChoice:'input',scanSizeScale:100,scanWidthScale:100,scanXOffset:0,scanYOffset:0,
  scanDarkness:0,scanStroke:0,scanClarity:0,scanCleanup:50,scanEdgeBlend:0
});
function applyTuneNumberInput(id,finalize=false){const meta=SCAN_TUNE_META[id];if(!meta)return;const input=els[meta.inputId],range=els[id];if(!input||!range)return;const raw=String(input.value??'').trim();if(!raw||raw==='-'||raw==='+'){if(finalize)input.value=tuneNumber(range.value,meta.digits||1);return;}const parsed=Number(raw);if(!Number.isFinite(parsed)){if(finalize)input.value=tuneNumber(range.value,meta.digits||1);return;}range.value=tuneNumber(clampTuneValue(id,parsed),meta.digits||1);renderScanTuneValues();if(state.selected?.item?.engine==='scan'){updatePrecisionMode();markRunPending();}}
function resetOneScanTune(id){
  const el=els[id]||document.getElementById(id);if(!el||!(id in SCAN_TUNE_DEFAULT_BY_ID))return;
  el.value=SCAN_TUNE_DEFAULT_BY_ID[id];renderScanTuneValues();updatePrecisionMode();markRunPending();toast(`已复位${el.closest('.tune-row')?.querySelector('label span')?.textContent||'参数'}`);
}
function copyScanTuneParams(){
  if(state.selected?.item?.engine!=='scan')return toast('请先选择扫描文字');
  state.scanTuneClipboard=readScanVisualAdjust();
  try{localStorage.setItem('pedit.oss.scanTuneClipboard',JSON.stringify(state.scanTuneClipboard));}catch{}
  toast('已复制全部视觉微调参数');
}
function pasteScanTuneParams(){
  if(state.selected?.item?.engine!=='scan')return toast('请先选择扫描文字');
  let a=state.scanTuneClipboard;
  if(!a){try{a=JSON.parse(localStorage.getItem('pedit.oss.scanTuneClipboard')||'null');}catch{}}
  if(!a)return toast('还没有复制视觉微调参数');
  loadScanVisualAdjust(a);updatePrecisionMode();markRunPending();toast('已粘贴全部视觉微调参数，请应用并预览');
}

function renderFinishedGlyphLibrary(){
  if(!els.finishedGlyphLibrary)return;els.finishedGlyphLibrary.innerHTML='';
  if(!state.glyphLibrary?.size){els.finishedGlyphLibrary.innerHTML='<span class="finished-glyph-empty">当前文档字库为空</span>';return;}
  for(const [ch,clip] of state.glyphLibrary.entries()){const b=document.createElement('button');b.type='button';b.className='finished-glyph-chip'+(state.glyphClipboard?.asset?.assetId===clip.asset?.assetId?' active':'');b.title=`选择成品字 ${ch}`;b.innerHTML=`<span>${escapeHtml(ch)}</span><small>${clip.mode==='fit'?'适配':'原样'}</small>`;b.onclick=()=>{state.glyphClipboard=clip;if(els.finishedGlyphMode)els.finishedGlyphMode.value=clip.mode||'original';renderFinishedGlyphLibrary();toast(`已选择成品字“${ch}”`);};els.finishedGlyphLibrary.appendChild(b);}
}
function buildGlyphClipFromAsset(edit,reusableGlyph,mode){const d=singleCharDiff(edit?.oldText,edit?.newText);if(!d||!reusableGlyph)return null;const existing=state.glyphLibrary.get(d.newChar);const assetId=reusableGlyph.assetId||existing?.asset?.assetId||`${state.id}:${edit.page}:${edit.id}:${d.index}:${Date.now()}`;const finalMode=mode||reusableGlyph.mode||existing?.mode||'original';const payload={...reusableGlyph,assetId,mode:finalMode,char:d.newChar};return {documentId:state.id,char:d.newChar,index:d.index,oldChar:d.oldChar,sourceOldText:edit.oldText,sourceNewText:edit.newText,mode:finalMode,asset:payload};}
function autoReusableGlyphFor(item,newText){if(!state.id||!item)return undefined;const d=singleCharDiff(item.text,newText);if(!d)return undefined;const clip=state.glyphLibrary.get(d.newChar);if(!clip||clip.documentId!==state.id||!clip.asset?.dataUrl)return undefined;return {...clip.asset,mode:clip.mode||'original',char:clip.char};}
function rememberPreferredGlyph(edit,layoutMetrics){const clip=buildGlyphClipFromAsset(edit,layoutMetrics?.reusableGlyph,edit?.reusableGlyph?.mode||state.glyphLibrary.get(singleCharDiff(edit?.oldText,edit?.newText)?.newChar||'')?.mode||'original');if(!clip)return;const existing=state.glyphLibrary.get(clip.char);const manual=!!edit?.reusableGlyph||!scanAdjustIsDefault(edit?.visualAdjust||{})||String((edit?.visualAdjust||{}).fontChoice||'auto')!=='auto';if(!existing||manual)state.glyphLibrary.set(clip.char,clip);if(!existing&&(!state.glyphClipboard||state.glyphClipboard.char===clip.char))state.glyphClipboard=clip;renderFinishedGlyphLibrary();}
function copyFinishedGlyph(){
  if(state.selected?.type!=='text'||state.selected.item.engine!=='scan')return toast('请先选择已经运行成功的扫描文字');
  const key=state.selected.key,edit=state.edits.get(key),f=state.feasibility.get(key);if(!edit||!f)return toast('当前文字还没有运行成功，无法复制成品字');
  const d=singleCharDiff(edit.oldText,edit.newText);const asset=f.layoutMetrics?.reusableGlyph;if(!d||!asset)return toast('成品字复用目前要求一次只替换一个字符');
  const mode=els.finishedGlyphMode?.value||'original';const assetId=`${state.id}:${edit.page}:${edit.id}:${d.index}:${Date.now()}`;const payload={...asset,assetId,mode,char:d.newChar};
  const clip={documentId:state.id,char:d.newChar,index:d.index,oldChar:d.oldChar,sourceOldText:edit.oldText,sourceNewText:edit.newText,mode,asset:payload};state.glyphClipboard=clip;state.glyphLibrary.set(d.newChar,clip);renderFinishedGlyphLibrary();toast(`已复制成品字“${d.newChar}”，可粘贴到当前 PDF 其他位置`);
}
function pasteFinishedGlyph(){
  if(state.selected?.type!=='text'||state.selected.item.engine!=='scan')return toast('请先选择要粘贴到的扫描文字');const clip=state.glyphClipboard;if(!clip)return toast('还没有复制或选择成品字');if(clip.documentId!==state.id)return toast('成品字仅在当前 PDF 内复用');
  const item=state.selected.item,old=String(item.text||'');let next=String(els.textContent.value||old),idx=-1;const current=singleCharDiff(old,next);
  if(current&&current.newChar===clip.char)idx=current.index;else if(old.length>clip.index&&old[clip.index]===clip.oldChar){idx=clip.index;next=old.slice(0,idx)+clip.char+old.slice(idx+1);}else{const positions=[...old].map((c,i)=>c===clip.oldChar?i:-1).filter(i=>i>=0);if(positions.length===1){idx=positions[0];next=old.slice(0,idx)+clip.char+old.slice(idx+1);}}
  if(idx<0)return toast(`无法自动确定替换位置：请先在“修改为”中把目标字符改成“${clip.char}”，再粘贴成品字`,5200);
  const mode=els.finishedGlyphMode?.value||clip.mode||'original';const payload={...clip.asset,mode,char:clip.char};state.pendingReusableGlyph={key:state.selected.key,payload};els.textContent.value=next;updatePrecisionMode();markRunPending();renderFinishedGlyphLibrary();toast(`已粘贴成品字“${clip.char}”，点击开始运行即可应用`);
}

const ALLOWED_EDIT_MODES=new Set(['stream','docglyph','glyph','scanrevision','page-number-add','page-number-replace','free-text','none']);
function editModeAllowed(f){return !!f&&ALLOWED_EDIT_MODES.has(f.mode)&&f.visualVerified!==false;}
function setRunProcess(stateName='idle',step=0,title='等待运行',message='修改文字后，点击“开始运行”。',progress=0){
  if(!els.runProcess)return;
  if(state.pageProgressActive)setPageLoading(title,progress);
  els.runProcess.dataset.state=stateName;els.runStatusTitle.textContent=title;els.runProgressText.textContent=`${Math.max(0,Math.min(100,Math.round(progress)))}%`;els.runProgressBar.style.width=`${Math.max(0,Math.min(100,progress))}%`;els.runMessage.textContent=message||'';
  [...els.runSteps.querySelectorAll('li')].forEach(li=>{const n=+li.dataset.step;li.classList.remove('active','done','failed');if(stateName==='error'&&n===step)li.classList.add('failed');else if(n<step||(stateName==='success'&&n<=step))li.classList.add('done');else if(stateName==='running'&&n===step)li.classList.add('active');});
}
function renderFeasibilityStatus(j){
  if(!j){els.precisionMode.textContent='待运行 · 尚未执行修订检查';els.precisionMode.dataset.mode='pending';return;}
  if(j.mode==='scanrevision'){const m=j.layoutMetrics||{};const score=m.overall_match_score;els.precisionMode.textContent=`${m.qualityWarning||'已生成局部补丁 · 请检查放大对比'}${Number.isFinite(score)?` · 匹配 ${score} 分`:''}`;els.precisionMode.dataset.mode=m.qualityWarning?'pending':'exact';}
  else if(j.mode==='stream'){els.precisionMode.textContent='✓ 可修订 · 电子文字定位与版式检查通过';els.precisionMode.dataset.mode='exact';}
  else if(j.mode==='docglyph'){els.precisionMode.textContent='✓ 可修订 · 电子文字资源可用';els.precisionMode.dataset.mode='exact';}
  else if(j.mode==='glyph'){els.precisionMode.textContent='✓ 可修订 · 电子文字字形可用';els.precisionMode.dataset.mode='exact';}
  else if(j.mode==='free-text'){els.precisionMode.textContent='✓ 可新增 · 自由文字块位置有效';els.precisionMode.dataset.mode='exact';}
  else if(j.mode==='page-number-add'||j.mode==='page-number-replace'){els.precisionMode.textContent=`✓ 可编辑 · ${j.reason||'页码字块位置有效'}`;els.precisionMode.dataset.mode='exact';}
  else if(j.mode==='none'){els.precisionMode.textContent='✓ 未修改 · 保留原始内容';els.precisionMode.dataset.mode='exact';}
  else{els.precisionMode.textContent=`无法修订 · ${j.reason||'未通过检查'}`;els.precisionMode.dataset.mode='blocked';}
}
function currentDraft(){if(state.selected?.type!=='text')return null;return buildTextEdit(state.selected.item);}
function reusableGlyphEqual(a,b){return String(a?.assetId||'')===String(b?.assetId||'')&&String(a?.mode||'')===String(b?.mode||'');}
function storedMatchesDraft(edit,key){const s=state.edits.get(key);if(!s)return edit.newText===edit.oldText&&edit.sameStyle&&scanAdjustIsDefault(edit.visualAdjust)&&!edit.reusableGlyph;return s.newText===edit.newText&&s.size===edit.size&&s.color===edit.color&&s.x===edit.x&&s.y===edit.y&&visualAdjustEqual(s.visualAdjust,edit.visualAdjust)&&reusableGlyphEqual(s.reusableGlyph,edit.reusableGlyph);}
function markRunPending(){
  if(state.selected?.type!=='text'||!els.runEditBtn)return;const edit=currentDraft(),key=state.selected.key;if(!edit)return;
  const matched=storedMatchesDraft(edit,key);els.runEditBtn.disabled=state.runBusy||matched;els.runEditLabel.textContent=matched?(state.edits.has(key)?'已运行':'无需运行'):'开始运行';
  if(!matched){setRunProcess('idle',0,'等待运行','文字已修改。点击“开始运行”后才会执行修订检查、生成预览并记录变更。',0);els.precisionMode.textContent='待运行 · 尚未应用到页面';els.precisionMode.dataset.mode='pending';}
}
async function requestPreviewBlob(pageEdits){
  const r=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,scale:desiredRenderScale(),edits:pageEdits})});
  if(!r.ok)throw new Error(await apiError(r));return await r.blob();
}
async function showPreviewBlob(blob){if(state.previewUrl)URL.revokeObjectURL(state.previewUrl);state.previewUrl=URL.createObjectURL(blob);await new Promise((resolve,reject)=>{els.pageImage.onload=()=>resolve();els.pageImage.onerror=()=>reject(new Error('修改预览图片加载失败'));els.pageImage.src=state.previewUrl;});}
async function requestComparisonBlob(pageEdits,bbox){
  const r=await fetch('/api/compare-crop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,bbox,edits:pageEdits})});
  if(!r.ok)throw new Error(await apiError(r));const changed=r.headers.get('X-Page-Changed')!=='0';return {blob:await r.blob(),changed};
}
function hideComparison(){if(els.compareSection)els.compareSection.classList.add('hidden');if(els.compareImage)els.compareImage.removeAttribute('src');if(els.compareNote)els.compareNote.textContent='运行完成后自动生成局部放大对比。';}
async function showComparisonBlob(blob,metrics){if(!els.compareSection||!els.compareImage)return;const url=URL.createObjectURL(blob);els.compareImage.onload=()=>URL.revokeObjectURL(url);els.compareImage.src=url;els.compareSection.classList.remove('hidden');if(els.compareNote){const m=metrics||{};const bits=[];if(Number.isFinite(+m.heightErrorPct))bits.push(`字高偏差 ${m.heightErrorPct}%`);if(Number.isFinite(+m.widthErrorPct))bits.push(`宽度偏差 ${m.widthErrorPct}%`);if(Number.isFinite(+m.baselineErrorPct))bits.push(`基线偏差 ${m.baselineErrorPct}%`);els.compareNote.textContent=bits.length?bits.join(' · '):'已生成局部放大对比。';}}
async function runSelectedEdit(){
  if(state.runBusy||state.selected?.type!=='text')return false;
  const {item,key}=state.selected,edit=buildTextEdit(item);
  if(edit.newText===edit.oldText&&edit.sameStyle&&scanAdjustIsDefault(edit.visualAdjust)){
    if(state.edits.has(key)){pushHistory('恢复文字原文',{page:edit.page+1,detail:edit.oldText});state.edits.delete(key);state.feasibility.delete(key);updateChangeCount();renderOverlays();await refreshPreview();}
    renderFeasibilityStatus({mode:'none',visualVerified:true});setRunProcess('success',5,'无需修改','当前内容与原文一致，页面保持原样。',100);markRunPending();return true;
  }
  clearTimeout(state.previewTimer);++state.renderToken;state.runBusy=true;els.runEditBtn.disabled=true;els.runEditLabel.textContent='运行中…';let runStep=1;
  setRunProcess('running',1,'步骤 1 / 5：定位字段','已收集当前文字和页面信息。',20);
  try{
    runStep=2;setRunProcess('running',2,'步骤 2 / 5：局部 OCR 校验','正在确认字段范围、OCR 边界和修订方式…',40);
    const f=await requestFeasibility(edit);
    if(!editModeAllowed(f))throw new Error(f?.reason||'该文字未通过修订检查');
    renderFeasibilityStatus(f);
    const detail=f.reason||'修订检查通过';
    runStep=3;setRunProcess('running',3,'步骤 3 / 5：生成修订内容',detail,60);
    const candidate=allEdits().filter(e=>!(e.type===edit.type&&e.page===edit.page&&e.id===edit.id));candidate.push(edit);
    const pageEdits=candidate.filter(e=>e.page===state.currentPage);
    runStep=4;setRunProcess('running',4,'步骤 4 / 5：重新渲染页面','正在生成字段级页面预览…',80);
    const blob=await requestPreviewBlob(pageEdits);
    const compare=await requestComparisonBlob(pageEdits,f.fieldBbox||edit.bbox);
    runStep=5;setRunProcess('running',5,'步骤 5 / 5：验证修改结果','正在验证目标区域像素实际变化…',90);
    if(!compare.changed)throw new Error('修改结果未成功写入页面。');
    pushHistory(`修改文字：${edit.oldText} → ${edit.newText}`,{page:edit.page+1,detail:edit.engine==='scan'?'扫描文字':'电子文字'});state.edits.set(key,edit);state.feasibility.set(key,{...f,newText:edit.newText,size:edit.size,color:edit.color,x:edit.x,y:edit.y,visualAdjust:edit.visualAdjust,reusableGlyph:edit.reusableGlyph});if(edit.engine==='scan')rememberPreferredGlyph(edit,f.layoutMetrics);await showPreviewBlob(blob);await showComparisonBlob(compare.blob,f.layoutMetrics);updateChangeCount();renderOverlays();
    const softWarn=f.layoutMetrics?.qualityWarning||'';
    setRunProcess('success',5,'运行完成',softWarn||'页面预览已更新；请在 100%/200% 下确认视觉协调。',100);
    toast(softWarn?`已生成预览：${softWarn}`:'已生成局部修改，请检查放大对比',4600);return true;
  }catch(e){
    renderFeasibilityStatus({mode:'blocked',visualVerified:false,reason:e.message});setRunProcess('error',runStep,'运行失败',e.message,runStep===3?78:46);toast(`运行失败：${e.message}`,6200);return false;
  }finally{state.runBusy=false;markRunPending();}
}

function updateEngineUi(){
  const kind=state.pageData?.pageKind||state.documentType||'unknown';
  if(kind==='scan'){
    const ready=state.pageData?.ocrAvailable!==false;
    const backend=state.pageData?.ocrBackendLabel||state.ocrBackendLabel||'内置 OCR';
    if(els.engineStatusText)els.engineStatusText.textContent=ready?`扫描 PDF · ${backend} · 修订模式`:'扫描 PDF · OCR 未就绪';
    if(els.documentModeHint)els.documentModeHint.textContent=ready?'OCR 负责定位；扫描文字会先做字高、宽度、基线与字距检查，再生成字段级修订预览':(state.pageData?.ocrReason||state.ocrReason||'OCR 组件未就绪');
    if(els.emptyPropsText)els.emptyPropsText.textContent=ready?'这是扫描 / 图片 PDF。点击识别出的文字即可修改。':'这是扫描 / 图片 PDF，但 OCR 组件没有成功启动。';
    if(els.emptyPropsTip)els.emptyPropsTip.textContent=ready?'点击不同位置选择字段，或选择编辑整行；默认不添加修订标记。':'请重新双击 start_windows.bat；启动脚本会自动安装 OCR 依赖。';
  }else if(kind==='vector'){
    if(els.engineStatusText)els.engineStatusText.textContent='矢量 / 转曲 PDF';
    if(els.documentModeHint)els.documentModeHint.textContent='当前版本暂不把矢量轮廓当作文字编辑';
  }else{
    if(els.engineStatusText)els.engineStatusText.textContent='电子 PDF · 精准修订模式';
    if(els.documentModeHint)els.documentModeHint.textContent='Alt + 单击可切换重叠对象';
    if(els.emptyPropsText)els.emptyPropsText.textContent='点击文字进行修改，点击图片进行原位替换。';
    if(els.emptyPropsTip)els.emptyPropsTip.textContent='图片挡住文字时，将顶部“选择”切换为“只选文字”。';
  }
}

async function importPdf(file){
  if(!file)return;if(!file.name.toLowerCase().endsWith('.pdf'))return toast('请选择 PDF 文件');showLoading(true);
  try{
    const r=await fetch('/api/open',{method:'POST',headers:{'Content-Type':'application/pdf','X-Filename':encodeURIComponent(file.name)},body:file});
    if(!r.ok)throw new Error(await apiError(r));const j=await r.json();
    Object.assign(state,{id:j.id,name:j.name,outputName:j.outputName,pageCount:j.pageCount,currentPage:0,pageData:null,edits:new Map(),undo:[],redo:[],selected:null,zoom:1,viewMode:'fit-width',cleanPreview:false,feasibility:new Map(),selectionMode:'smart',cycleSig:'',cycleIndex:0,batchMatches:[],batchSource:null,runBusy:false,changeLogExport:false,glyphClipboard:null,glyphLibrary:new Map(),pendingReusableGlyph:null,blockClipboard:null,blockLibrary:new Map(),pageNumberMatches:[],pageNumberScanResults:[],pageNumberTemplates:{A:null,B:null},pageNumberManualTakeovers:new Set(),documentType:j.documentType||'unknown',diagnosis:j.diagnosis||null,ocrAvailable:!!j.ocrAvailable,ocrReason:j.ocrReason||'',ocrLang:j.ocrLang||'',ocrBackend:j.ocrBackend||'',ocrBackendLabel:j.ocrBackendLabel||'',versionHistory:[],versionSeq:0,historySelectedId:null,pendingHistoryLabel:null,pendingHistoryMeta:null,changeLogSelectedKeys:new Set(),exportSelectedKeys:new Set(),changeLogTombstones:[],changeLogFilter:'all',previewQuality:'auto',lastRenderScale:1.7,currentBaselineId:Number(j.baselineId||0),baselineSeq:Number(j.baselineId||0),pageRenderStatus:new Map(),resolvedAnomalyPages:new Set()});
    els.selectionMode.value='smart';
    els.welcome.classList.add('hidden');els.viewer.classList.remove('hidden');els.pagesPanel.classList.remove('hidden');els.propertiesPanel.classList.remove('hidden');
    els.exportBtn.disabled=false;if(els.saveProgressBtn)els.saveProgressBtn.disabled=false;if(els.saveContinueBtn)els.saveContinueBtn.disabled=false;if(els.changeLogBtn)els.changeLogBtn.disabled=false;if(els.pageNumberBtn)els.pageNumberBtn.disabled=false;if(els.historyBtn)els.historyBtn.disabled=false;els.fileNameLabel.textContent=j.name;if(els.topFileName)els.topFileName.textContent=j.name;if(els.documentPill){const dot=els.documentPill.querySelector('.document-dot');if(dot)dot.style.background='#35a566';}els.pageCountBadge.textContent=j.pageCount;els.totalPagesLabel.textContent=j.pageCount;
    updateChangeCount();updateHistoryButtons();clearProps();buildThumbnails();updateEngineUi();await loadPage(0);captureVersion('导入文档',{page:1,detail:j.name},true);if(state.documentType==='scan')toast(state.ocrAvailable?`已识别为扫描 PDF，${state.ocrBackendLabel||'内置 OCR'} 已启用。`:'已识别为扫描 PDF，但 OCR 组件未就绪；请重新运行启动脚本自动安装。',4800);else toast('PDF 已导入，已自动适应宽度。');
  }catch(e){toast(e.message,3500);}finally{showLoading(false);}
}

function buildThumbnails(){
  els.thumbList.innerHTML='';
  for(let i=0;i<state.pageCount;i++){
    const d=document.createElement('div');d.className='thumb'+(i===0?' active':'');d.dataset.page=i;
    const img=document.createElement('img');img.loading='lazy';img.src=`/api/page?id=${state.id}&page=${i}&scale=.35`;
    const n=document.createElement('div');n.className='num';n.textContent=`第 ${i+1} 页`;
    d.append(img,n);d.onclick=()=>loadPage(i);els.thumbList.appendChild(d);
  }
  updateChangeCount();
}

async function loadPage(page){
  if(page<0||page>=state.pageCount)return;state.currentPage=page;state.selected=null;state.cycleSig='';clearProps();
  els.currentPageLabel.textContent=page+1;if(els.statusPageMirror)els.statusPageMirror.textContent=page+1;els.prevPage.disabled=page===0;els.nextPage.disabled=page===state.pageCount-1;
  document.querySelectorAll('.thumb').forEach(x=>x.classList.toggle('active',+x.dataset.page===page));
  showLoading(true);const token=++state.renderToken;
  try{
    const r=await fetch(`/api/page-data?id=${state.id}&page=${page}`);if(!r.ok)throw new Error(await apiError(r));const j=await r.json();
    if(token!==state.renderToken)return;state.pageData=j;if(j.ocrBackend)state.ocrBackend=j.ocrBackend;if(j.ocrBackendLabel)state.ocrBackendLabel=j.ocrBackendLabel;updateEngineUi();if(j.scanMode&&j.ocrAvailable!==false&&(!j.text||!j.text.length))toast('本页 OCR 已运行，但没有识别到可编辑文字。',3600);
    applyViewMode(true);const renderScale=desiredRenderScale();state.lastRenderScale=renderScale;
    els.pageImage.src=`/api/page?id=${state.id}&page=${page}&scale=${renderScale}&v=${Date.now()}`;
    await new Promise((res,rej)=>{els.pageImage.onload=res;els.pageImage.onerror=rej;});if(token!==state.renderToken)return;
    await new Promise(res=>requestAnimationFrame(()=>requestAnimationFrame(res)));if(token!==state.renderToken)return;
    applyViewMode(true);renderOverlays();schedulePreview(0);
  }catch(e){toast(e.message,3500);}finally{showLoading(false);}
}

function sizePage(){
  if(!state.pageData)return;
  const w=state.pageData.width*state.scale*state.zoom,h=state.pageData.height*state.scale*state.zoom;
  for(const el of [els.pageImage,els.pageWrap]){el.style.width=`${w}px`;el.style.height=`${h}px`;}
  els.pageWrap.style.transform='none';els.pageWrap.style.marginBottom='0';
  els.zoomLabel.textContent=`${Math.round(state.zoom*100)}%`;
  if(els.statusZoomMirror)els.statusZoomMirror.textContent=els.zoomLabel.textContent;
  renderOverlays();
}
function viewportSpace(){const s=getComputedStyle(els.pageScroll);return {w:els.pageScroll.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)-2,h:els.pageScroll.clientHeight-parseFloat(s.paddingTop)-parseFloat(s.paddingBottom)-2};}
function calculateFitWidthZoom(){return viewportSpace().w/(state.pageData.width*state.scale);}
function calculateFitPageZoom(){return Math.min(calculateFitWidthZoom(),viewportSpace().h/(state.pageData.height*state.scale));}
function centerPage(){if(!els.pageWrap||!els.pageScroll)return;const left=els.pageWrap.offsetLeft,width=els.pageWrap.offsetWidth,client=els.pageScroll.clientWidth;els.pageScroll.scrollLeft=Math.max(0,left+width/2-client/2);}
function resetViewport(){els.pageScroll.scrollTop=0;centerPage();}
function applyViewMode(reset=false){
  if(!state.pageData)return;
  if(state.viewMode!=='custom')state.zoom=Math.max(.01,state.viewMode==='fit-width'?calculateFitWidthZoom():calculateFitPageZoom());
  sizePage();if(reset){resetViewport();requestAnimationFrame(()=>{resetViewport();requestAnimationFrame(centerPage);});}
}
function setViewMode(mode){state.viewMode=mode;applyViewMode(true);}
function fitPage(){setViewMode('fit-page');}
function fitWidth(){setViewMode('fit-width');}
function restoreCustomZoom(zoom){state.zoom=Math.min(4,Math.max(.05,zoom));setViewMode('custom');}
function toPx(v){return v*state.scale*state.zoom;}
let resizeTimer;
new ResizeObserver(()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(state.viewMode!=='custom')applyViewMode(true);},120);}).observe(els.pageScroll);

function fieldAtPoint(line,x,y){
  const s=(line.subfields||[]).find(f=>f.bbox&&pointInBbox(x,y,f.bbox,0));
  if(!s)return line;
  return {...line,id:`${line.id}::${s.start}-${s.end}`,lineId:line.id,text:s.text,bbox:s.bbox,chars:s.chars,tokenBbox:line.bbox,sourceText:line.text,subfieldKind:s.kind,characterGeometry:s.geometry==='character'};
}
function pointInBbox(x,y,b,tol=0.8){return x>=b[0]-tol&&x<=b[2]+tol&&y>=b[1]-tol&&y<=b[3]+tol;}

function candidatesAtEvent(e){
  const d=state.pageData;if(!d)return[];const rect=els.pageWrap.getBoundingClientRect();
  const x=(e.clientX-rect.left)/(state.zoom*state.scale),y=(e.clientY-rect.top)/(state.zoom*state.scale);
  let c=[];
  if(state.selectionMode!=='image')for(const item of d.text)if(pointInBbox(x,y,item.bbox)){const picked=item.engine==='scan'?fieldAtPoint(item,x,y):item;c.push({type:'text',item:picked,key:editKey('text',state.currentPage,picked.id)});}
  const suppressScanBackground=d.scanMode&&state.selectionMode==='smart';
  if(state.selectionMode!=='text'&&!suppressScanBackground)for(const item of d.images)if(pointInBbox(x,y,item.bbox))c.push({type:'image',item,key:editKey('image',state.currentPage,item.id)});
  if(state.selectionMode==='smart')c.sort((a,b)=>a.type===b.type?0:(a.type==='text'?-1:1));
  return c;
}
function selectAtPoint(e){
  e.stopPropagation();const c=candidatesAtEvent(e);if(!c.length)return;
  let pick=c[0];
  if(e.altKey&&c.length>1){
    const sig=c.map(x=>x.key).join('|');if(sig===state.cycleSig)state.cycleIndex=(state.cycleIndex+1)%c.length;else{state.cycleSig=sig;state.cycleIndex=1%c.length;}pick=c[state.cycleIndex];
    toast(`重叠对象 ${state.cycleIndex+1}/${c.length}：${pick.type==='text'?'文字':'图片'}`,1200);
  }else{state.cycleSig='';state.cycleIndex=0;}
  selectObject(pick.type,pick.item,pick.key);
}

function renderOverlays(){
  const d=state.pageData;if(!d)return;els.overlayLayer.className=`overlay-layer mode-${state.selectionMode}${state.cleanPreview?' clean-preview':''}`;els.overlayLayer.innerHTML='';if(state.cleanPreview)return;
  const selectedKey=state.selected?.key;
  for(const item of d.text){
    const key=editKey('text',state.currentPage,item.id),box=document.createElement('div');box.className='obj-box text-box';if(state.edits.has(key))box.classList.add('edited');if((key===selectedKey||item.id===state.selected?.item?.lineId))box.classList.add('selected');
    const f=state.feasibility.get(key);
    const drawBbox=(item.engine==='scan'&&(key===selectedKey||item.id===state.selected?.item?.lineId)&&Array.isArray(f?.fieldBbox)&&f.fieldBbox.length===4)?f.fieldBbox:(item.id===state.selected?.item?.lineId?state.selected.item.bbox:item.bbox);
    const [x0,y0,x1,y1]=drawBbox;Object.assign(box.style,{left:`${toPx(x0)}px`,top:`${toPx(y0)}px`,width:`${Math.max(3,toPx(x1-x0))}px`,height:`${Math.max(4,toPx(y1-y0))}px`});box.title=`文字：${item.text}${state.selectionMode==='smart'?' · Alt+单击切换重叠对象':''}`;box.dataset.key=key;box.setAttribute('aria-hidden','true');els.overlayLayer.appendChild(box);
  }
  for(const item of d.images){
    const key=editKey('image',state.currentPage,item.id),box=document.createElement('div');box.className='obj-box image-box';if(state.edits.has(key))box.classList.add('edited');if((key===selectedKey||item.id===state.selected?.item?.lineId))box.classList.add('selected');
    const [x0,y0,x1,y1]=item.bbox;Object.assign(box.style,{left:`${toPx(x0)}px`,top:`${toPx(y0)}px`,width:`${Math.max(3,toPx(x1-x0))}px`,height:`${Math.max(4,toPx(y1-y0))}px`});box.title=`图片${state.selectionMode==='smart'?' · Alt+单击切换重叠对象':''}`;box.dataset.key=key;box.setAttribute('aria-hidden','true');els.overlayLayer.appendChild(box);
  }
}

function scanPreviewFontFamily(choice){
  const map={input:'"Segoe UI",Arial,"Microsoft YaHei",sans-serif',auto:'"Segoe UI",Arial,"Microsoft YaHei",sans-serif',times:'"Times New Roman",Times,serif',arial:'Arial,"Microsoft YaHei",sans-serif',calibri:'Calibri,Arial,sans-serif',cambria:'Cambria,"Times New Roman",serif',simsun:'SimSun,"宋体",serif',msyh:'"Microsoft YaHei","微软雅黑",sans-serif'};
  return map[choice]||map.input;
}
function updateFinalGlyphPreview(){
  if(!els.finalGlyphPreviewCard)return;const scan=state.selected?.type==='text'&&state.selected?.item?.engine==='scan';
  els.finalGlyphPreviewCard.classList.toggle('hidden',!scan);if(!scan)return;
  const choice=els.scanFontChoice?.value||'input',text=String(els.textContent?.value||'');
  els.finalGlyphPreviewText.textContent=text||'—';els.finalGlyphPreviewText.style.fontFamily=scanPreviewFontFamily(choice);
  const labels={input:'保持输入字形',auto:'自动匹配',times:'Times',arial:'Arial',calibri:'Calibri',cambria:'Cambria',simsun:'宋体',msyh:'微软雅黑'};
  els.finalGlyphPreviewMode.textContent=labels[choice]||'保持输入字形';
  els.finalGlyphPreviewHint.textContent=choice==='input'?'所见即所得模式：固定字形；超出原字段时会提示调整，不再后台自动换字体或明显压扁。':'自动匹配模式：允许根据原扫描字形选择更接近的系统字体。';
}
function selectObject(type,item,key){
  if(state.cleanPreview)return;
  state.selected={type,item,key};const stored=state.edits.get(key);state.pendingReusableGlyph=stored?.reusableGlyph?{key,payload:stored.reusableGlyph}:null;renderOverlays();showSelectedProps();
}
function clearProps(){state.selected=null;state.pendingReusableGlyph=null;hideComparison();els.objectType.textContent='未选择';els.emptyProps.classList.remove('hidden');els.textProps.classList.add('hidden');els.imageProps.classList.add('hidden');els.scanTuneSection?.classList.add('hidden');els.finalGlyphPreviewCard?.classList.add('hidden');[els.fontSize,els.fontColor,els.textX,els.textY].forEach(x=>x.disabled=false);updateEngineUi();}
function showSelectedProps(){
  if(!state.selected)return clearProps();const {type,item,key}=state.selected;const edit=state.edits.get(key);els.emptyProps.classList.add('hidden');
  if(type==='text'){
    const scan=item.engine==='scan';els.objectType.textContent=scan?'扫描文字':'文字';els.textProps.classList.remove('hidden');els.imageProps.classList.add('hidden');els.scanFieldInfo.classList.toggle('hidden',!scan);els.replaceLabel.classList.toggle('hidden',!scan);if(scan){els.ocrOriginal.textContent=item.sourceText||item.text;els.currentOcrField.textContent=item.text;}els.textContent.value=edit?.action==='delete'?item.text:(edit?.newText??item.text);els.fontSize.value=edit?.size??item.size;els.fontColor.value=edit?.color??item.color;els.fontName.value=scan?'扫描 OCR 修订':(item.font||'未识别');els.textX.value=edit?.x??item.origin[0];els.textY.value=edit?.y??item.origin[1];[els.fontSize,els.fontColor,els.textX,els.textY].forEach(x=>x.disabled=scan);els.scanTuneSection?.classList.toggle('hidden',!scan);if(scan){loadScanVisualAdjust(edit?.visualAdjust);updateFinalGlyphPreview();}if(edit){const ef=state.feasibility.get(key);renderFeasibilityStatus(ef);setRunProcess('success',5,'已运行','当前修订已经生成页面预览并加入修订记录。',100);requestComparisonBlob(allEdits().filter(e=>e.page===state.currentPage),ef?.fieldBbox||edit.bbox).then(x=>x.changed&&showComparisonBlob(x.blob,ef?.layoutMetrics)).catch(()=>{});}else{hideComparison();updatePrecisionMode();setRunProcess('idle',0,'等待运行','修改文字后，点击“开始运行”。',0);}markRunPending();
  }else{
    [els.fontSize,els.fontColor,els.textX,els.textY].forEach(x=>x.disabled=false);
    els.scanTuneSection?.classList.add('hidden');els.objectType.textContent='图片';els.imageProps.classList.remove('hidden');els.textProps.classList.add('hidden');els.imageFit.value=edit?.fit||'contain';if(edit?.action==='delete'){els.replacementPreview.classList.add('hidden');els.imagePlaceholder.classList.remove('hidden');els.imagePlaceholder.textContent='已标记删除';}else if(edit?.dataUrl){els.replacementPreview.src=edit.dataUrl;els.replacementPreview.classList.remove('hidden');els.imagePlaceholder.classList.add('hidden');}else{els.replacementPreview.classList.add('hidden');els.imagePlaceholder.classList.remove('hidden');els.imagePlaceholder.textContent='原图片区域';}
  }
}

function singleCharDiff(oldText,newText){
  oldText=String(oldText||'');newText=String(newText||'');if(oldText.length!==newText.length)return null;const idx=[];for(let i=0;i<oldText.length;i++)if(oldText[i]!==newText[i])idx.push(i);if(idx.length!==1)return null;const i=idx[0];return {index:i,oldChar:oldText[i],newChar:newText[i]};
}
function reusableApplies(oldText,newText,payload){const d=singleCharDiff(oldText,newText);return !!d&&!!payload&&String(payload.char||'')===d.newChar;}

function buildTextEdit(item){
  const size=+els.fontSize.value||item.size,color=els.fontColor.value,x=+els.textX.value,y=+els.textY.value;
  const sameStyle=Math.abs(size-item.size)<.001&&color.toLowerCase()===item.color.toLowerCase()&&Math.abs(x-item.origin[0])<.001&&Math.abs(y-item.origin[1])<.001;
  const engine=item.engine||'electronic',visualAdjust=engine==='scan'?readScanVisualAdjust():undefined;
  const pending=(engine==='scan'&&state.pendingReusableGlyph?.key===state.selected?.key)?state.pendingReusableGlyph.payload:undefined;let reusableGlyph=reusableApplies(item.text,els.textContent.value,pending)?pending:undefined;if(engine==='scan'&&!reusableGlyph)reusableGlyph=autoReusableGlyphFor(item,els.textContent.value);return {type:'text',engine,page:state.currentPage,id:item.id,bbox:item.bbox,tokenBbox:item.tokenBbox||item.bbox,manualSelection:!!item.manualSelection,characterGeometry:!!item.characterGeometry,requiresIsolation:!!(item.sourceText&&item.sourceText!==item.text),origin:item.origin,oldText:item.text,newText:els.textContent.value,font:item.font,size,color,x,y,rotation:item.rotation||0,alpha:item.alpha??255,chars:item.chars||[],sameStyle,fontEmbedded:!!item.fontEmbedded,...(engine==='scan'?{visualAdjust,...(reusableGlyph?{reusableGlyph}:{})}: {})};
}
function targetEditFromMatch(match,newText){
  const item=match.item;
  const engine=item.engine||'electronic';const batchReusable=engine==='scan'?(reusableApplies(item.text,newText,state.batchSource?.reusableGlyph)?state.batchSource?.reusableGlyph:autoReusableGlyphFor(item,newText)):undefined;return {type:'text',engine,page:match.page,id:item.id,bbox:item.bbox,origin:item.origin,oldText:item.text,newText,font:item.font,size:item.size,color:item.color,x:item.origin[0],y:item.origin[1],rotation:item.rotation||0,alpha:item.alpha??255,chars:item.chars||[],sameStyle:true,fontEmbedded:!!item.fontEmbedded,...(engine==='scan'?{visualAdjust:normalizeScanVisualAdjust(state.batchSource?.visualAdjust),...(batchReusable?{reusableGlyph:batchReusable}:{})}:{})};
}

function updatePrecisionMode(){
  if(state.selected?.type!=='text'||!els.precisionMode)return;const item=state.selected.item,edit=buildTextEdit(item),key=state.selected.key;
  if(storedMatchesDraft(edit,key)){const f=state.feasibility.get(key);if(state.edits.has(key)&&f)renderFeasibilityStatus(f);else{els.precisionMode.textContent=item.engine==='scan'?'✓ 未修改 · 保留原扫描像素':'✓ 未修改 · 保留原始内容';els.precisionMode.dataset.mode='exact';}return;}
  if(!edit.sameStyle){els.precisionMode.textContent='待运行 · 已修改样式/位置，可能无法通过精准修订检查';els.precisionMode.dataset.mode='blocked';}
  else if(item.engine==='scan'&&!scanAdjustIsDefault(edit.visualAdjust)){els.precisionMode.textContent='待运行 · 已调整扫描文字视觉参数';els.precisionMode.dataset.mode='pending';}
  else{els.precisionMode.textContent='待运行 · 点击“开始运行”执行检查并更新页面';els.precisionMode.dataset.mode='pending';}
}
async function requestFeasibility(edit){const r=await fetch('/api/feasibility',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,edit})});if(!r.ok)throw new Error(await apiError(r));return await r.json();}
async function checkFeasibility(edit,key){
  if(!edit||edit.newText===edit.oldText&&edit.sameStyle&&scanAdjustIsDefault(edit.visualAdjust)){state.feasibility.delete(key);return null;}const token=++state.feasibilityToken;
  try{
    const j=await requestFeasibility(edit);state.feasibility.set(key,{...j,newText:edit.newText,size:edit.size,color:edit.color,x:edit.x,y:edit.y,visualAdjust:edit.visualAdjust,reusableGlyph:edit.reusableGlyph});
    if(token===state.feasibilityToken&&state.selected?.key===key){
      renderFeasibilityStatus(j);renderOverlays();
    }return j;
  }catch(e){if(state.selected?.key===key){els.precisionMode.textContent=`检查失败 · ${e.message}`;els.precisionMode.dataset.mode='blocked';}return null;}
}

function commitTextChange(){
  if(state.selected?.type!=='text')return;const {item,key}=state.selected,edit=buildTextEdit(item),isOriginal=edit.newText===item.text&&edit.sameStyle&&scanAdjustIsDefault(edit.visualAdjust);pushHistory(isOriginal?'恢复文字原文':`编辑文字：${edit.oldText} → ${edit.newText}`,{page:edit.page+1});
  if(isOriginal){state.edits.delete(key);state.feasibility.delete(key);updateChangeCount();renderOverlays();updatePrecisionMode();schedulePreview(0);}
  else{state.edits.set(key,edit);updateChangeCount();renderOverlays();updatePrecisionMode();checkFeasibility(edit,key).then(()=>schedulePreview(0));}
}

async function commitImage(file){
  if(state.selected?.type!=='image'||!file)return;if(!file.type.startsWith('image/'))return toast('请选择图片文件');
  const dataUrl=await new Promise((resolve,reject)=>{const fr=new FileReader();fr.onload=()=>resolve(fr.result);fr.onerror=reject;fr.readAsDataURL(file);});const dims=await imageDimensionsFromDataUrl(dataUrl);const {item,key}=state.selected;pushHistory('替换图片',{page:state.currentPage+1,detail:file.name});state.edits.set(key,{type:'image',page:state.currentPage,id:item.id,bbox:item.bbox,pdfBbox:item.pdfBbox||item.bbox,dataUrl,fit:els.imageFit.value,name:file.name,sourceWidth:dims.width,sourceHeight:dims.height,sourceBytes:file.size||0});updateChangeCount();renderOverlays();showSelectedProps();schedulePreview();
}
function resetSelected(type){if(state.selected?.type!==type)return;hideComparison();const key=state.selected.key;if(!state.edits.has(key))return;pushHistory(type==='text'?'恢复文字原文':'取消图片替换',{page:state.currentPage+1});state.edits.delete(key);state.feasibility.delete(key);updateChangeCount();renderOverlays();showSelectedProps();schedulePreview();}

function schedulePreview(delay=450){clearTimeout(state.previewTimer);++state.renderToken;if(!state.id)return;state.previewTimer=setTimeout(()=>refreshPreview().catch(()=>{}),delay);}
async function refreshPreview(){
  const pageEdits=allEdits().filter(e=>e.page===state.currentPage);
  const id=state.id,page=state.currentPage,scale=desiredRenderScale(),token=++state.renderToken;state.lastRenderScale=scale;
  showLoading(true);
  try{
    for(const edit of pageEdits.filter(e=>e.type==='text'&&e.action!=='delete')){
      const key=editKey('text',edit.page,edit.id);let f=state.feasibility.get(key);
      const stale=!f||f.newText!==edit.newText||f.size!==edit.size||f.color!==edit.color||f.x!==edit.x||f.y!==edit.y||!visualAdjustEqual(f.visualAdjust,edit.visualAdjust)||!reusableGlyphEqual(f.reusableGlyph,edit.reusableGlyph);
      if(stale){
        f=await requestFeasibility(edit);if(token!==state.renderToken)return;
        if(!editModeAllowed(f))throw new Error(f?.reason||'恢复修改未通过校验');
        state.feasibility.set(key,{...f,newText:edit.newText,size:edit.size,color:edit.color,x:edit.x,y:edit.y,visualAdjust:edit.visualAdjust,reusableGlyph:edit.reusableGlyph});
      }
      if(!editModeAllowed(f))throw new Error(f?.reason||'修改未通过校验');
    }
    const r=pageEdits.length
      ?await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,page,scale,edits:pageEdits})})
      :await fetch(`/api/page?id=${id}&page=${page}&scale=${scale}`);
    if(!r.ok)throw new Error(await apiError(r));
    const blob=await r.blob();if(token!==state.renderToken)return;
    await showPreviewBlob(blob);
    if(token===state.renderToken)state.previewReadyToken=token;
  }catch(e){if(token===state.renderToken)toast(`预览生成失败：${e.message}`,6200);throw e;}
  finally{if(token===state.renderToken)showLoading(false);}
}

function revisionRows(){
  return allEdits().slice().sort((a,b)=>(a.page-b.page)||String(a.type).localeCompare(String(b.type)));
}
function renderChangeLog(){
  const rows=revisionRows();const pages=new Set(rows.map(x=>x.page));
  if(els.changeLogSummary)els.changeLogSummary.textContent=rows.length?`${rows.length} 处修订 · ${pages.size} 页 · 导出后文末附修订记录`:'当前没有修改';
  if(!els.changeLogList)return;
  if(!rows.length){els.changeLogList.innerHTML='<div class="change-log-empty">当前没有修改。可以关闭清单继续编辑。</div>';return;}
  els.changeLogList.innerHTML=rows.map((e,i)=>{
    const isPageAdd=e.type==='page-number-add',isPageReplace=e.type==='page-number-replace',isFree=e.type==='free-text';const title=isFree?'自由文字':(isPageAdd?'新增页码':(isPageReplace?'页码原位修改':(e.action==='delete'?(e.type==='text'?'删除文字':'删除图片'):(e.type==='text'?'文字修订':'图片替换'))));
    const detail=(isPageAdd||isFree)?`<div class="change-log-diff"><span>新增</span><code>${escapeHtml(e.text||e.newText||'')}</code></div>`:(isPageReplace?`<div class="change-log-diff"><span>原</span><code>${escapeHtml(e.oldText||'')}</code><span>新</span><code>${escapeHtml(e.newText||'')}</code></div>`:(e.action==='delete'?`<div class="change-log-diff"><span>操作</span><code>${e.type==='text'?`删除：${escapeHtml(e.oldText||'文字')}`:'删除图片'}</code></div>`:(e.type==='text'?`<div class="change-log-diff"><span>原</span><code>${escapeHtml(e.oldText||'')}</code><span>新</span><code>${escapeHtml(e.newText||'')}</code></div>`:'<div class="change-log-diff"><span>操作</span><code>原位替换图片</code></div>')));
    return `<article class="change-log-item"><div class="change-log-index">${i+1}</div><div><strong>第 ${e.page+1} 页 · ${title}</strong>${detail}</div></article>`;
  }).join('');
}
function openChangeLog(forExport=false){
  if(!state.id)return;state.changeLogExport=!!forExport;renderChangeLog();els.changeLogConfirm.classList.toggle('hidden',!forExport);els.changeLogModal.classList.remove('hidden');
}
function closeChangeLog(){state.changeLogExport=false;els.changeLogModal.classList.add('hidden');}
async function performExportPdf(){
  if(!state.id)return;els.changeLogConfirm.disabled=true;els.exportBtn.disabled=true;els.exportBtn.textContent='生成修订版…';
  try{
    if(state.selected?.type==='text'){const draft=buildTextEdit(state.selected.item);if(!storedMatchesDraft(draft,state.selected.key))throw new Error('当前文字修订尚未运行，请先点击“开始运行”');}
    const edits=allEdits();for(const edit of edits.filter(e=>e.type==='text')){const key=editKey('text',edit.page,edit.id);let f=state.feasibility.get(key);const stale=!f||f.newText!==edit.newText||f.size!==edit.size||f.color!==edit.color||f.x!==edit.x||f.y!==edit.y||!visualAdjustEqual(f.visualAdjust,edit.visualAdjust)||!reusableGlyphEqual(f.reusableGlyph,edit.reusableGlyph);if(stale){f=await requestFeasibility(edit);state.feasibility.set(key,{...f,newText:edit.newText,size:edit.size,color:edit.color,x:edit.x,y:edit.y,visualAdjust:edit.visualAdjust,reusableGlyph:edit.reusableGlyph});}if(!editModeAllowed(f))throw new Error(`已阻止导出：第 ${edit.page+1} 页 · ${f.reason||'该文字未通过修订检查'}`);}
    const r=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,edits})});if(!r.ok)throw new Error(await apiError(r));const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=state.outputName||'修订版.pdf';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);closeChangeLog();toast(`已导出修订版：${a.download}`);
  }catch(e){toast(e.message,6200);}finally{els.changeLogConfirm.disabled=false;els.exportBtn.disabled=false;els.exportBtn.textContent='导出修订版';}
}
function exportPdf(){openChangeLog(true);}

// ---------- v1.6 batch page editing ----------
async function openBatchModal(){
  if(state.selected?.type!=='text')return toast('请先选择一个文字字段');
  const before=buildTextEdit(state.selected.item);
  if(before.newText===before.oldText)return toast('请先修改文字内容，再批量应用');
  if(!before.sameStyle)return toast(before.engine==='scan'?'扫描 PDF 批量编辑仅支持修改文字内容':'批量精准修订仅支持保持原字号、颜色和位置');
  if(!storedMatchesDraft(before,state.selected.key)){
    const ok=await runSelectedEdit();if(!ok)return;
  }
  const src=buildTextEdit(state.selected.item);state.batchSource=src;els.batchFieldSummary.textContent=`“${src.oldText}” → “${src.newText}”`;els.batchResult.classList.add('hidden');els.batchResult.textContent='';els.batchModal.classList.remove('hidden');scanBatchMatches();
}
function closeBatchModal(){if(state.batchBusy)return;els.batchModal.classList.add('hidden');}
async function scanBatchMatches(){
  if(!state.batchSource||state.batchBusy)return;state.batchBusy=true;els.batchConfirm.disabled=true;els.batchRescan.disabled=true;els.batchScanStatus.textContent='正在扫描全部页面的相同字段…';els.batchPageGrid.innerHTML='';
  try{
    const r=await fetch('/api/find-matches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,source:state.batchSource,samePosition:els.batchSamePosition.checked})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();state.batchMatches=j.matches||[];renderBatchPageGrid();
    els.batchScanStatus.textContent=`找到 ${state.batchMatches.length} 个匹配页面（共 ${state.pageCount} 页）`;
  }catch(e){els.batchScanStatus.textContent=`扫描失败：${e.message}`;toast(e.message,4500);}finally{state.batchBusy=false;els.batchConfirm.disabled=false;els.batchRescan.disabled=false;}
}
function renderBatchPageGrid(){
  const byPage=new Map(state.batchMatches.map(m=>[m.page,m]));els.batchPageGrid.innerHTML='';
  for(let p=0;p<state.pageCount;p++){
    const match=byPage.get(p),lab=document.createElement('label');lab.className='page-check'+(match?'':' disabled')+(p===state.currentPage?' current':'');const cb=document.createElement('input');cb.type='checkbox';cb.dataset.page=p;cb.disabled=!match;cb.checked=!!match;cb.onchange=()=>lab.classList.toggle('selected',cb.checked);lab.classList.toggle('selected',cb.checked);const span=document.createElement('span');span.textContent=`第 ${p+1} 页`;lab.append(cb,span);els.batchPageGrid.appendChild(lab);
  }
}
function batchCheckboxes(){return [...els.batchPageGrid.querySelectorAll('input[type=checkbox]:not(:disabled)')];}
function setBatchSelection(mode){const c=batchCheckboxes();for(const x of c){if(mode==='all')x.checked=true;else if(mode==='none')x.checked=false;else if(mode==='invert')x.checked=!x.checked;x.closest('.page-check').classList.toggle('selected',x.checked);}}
function parsePageRange(text,maxPage){
  const set=new Set();for(const raw of String(text||'').split(/[，,\s]+/).filter(Boolean)){const m=raw.match(/^(\d+)\s*[-~至]\s*(\d+)$/);if(m){let a=+m[1],b=+m[2];if(a>b)[a,b]=[b,a];for(let n=a;n<=b;n++)if(n>=1&&n<=maxPage)set.add(n-1);}else if(/^\d+$/.test(raw)){const n=+raw;if(n>=1&&n<=maxPage)set.add(n-1);}}return set;
}
function applyRangeSelection(){const set=parsePageRange(els.batchRange.value,state.pageCount);if(!set.size)return toast('没有识别到有效页码，例如：1-5,8,12-20');for(const x of batchCheckboxes()){x.checked=set.has(+x.dataset.page);x.closest('.page-check').classList.toggle('selected',x.checked);}toast(`已按范围选择 ${batchCheckboxes().filter(x=>x.checked).length} 个匹配页`);}
async function applyBatchEdits(){
  if(state.batchBusy||!state.batchSource)return;const selected=new Set(batchCheckboxes().filter(x=>x.checked).map(x=>+x.dataset.page));if(!selected.size)return toast('请至少选择一个匹配页面');const matches=state.batchMatches.filter(m=>selected.has(m.page)),lockedMatches=matches.filter(m=>{const k=editKey('text',m.page,m.item?.id||'');return state.edits.get(k)?.locked;}),editableMatches=matches.filter(m=>!lockedMatches.includes(m));const edits=editableMatches.map(m=>targetEditFromMatch(m,state.batchSource.newText));if(!edits.length)return toast(lockedMatches.length?'选中页面的匹配对象均已锁定':'没有可应用的匹配页面');
  state.batchBusy=true;els.batchConfirm.disabled=true;els.batchRescan.disabled=true;els.batchScanStatus.textContent=`正在逐页进行修订检查（${edits.length} 页）…`;
  try{
    const r=await fetch('/api/batch-feasibility',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,edits})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();const results=j.results||[];pushHistory(`批量修改 ${edits.length} 页`,{page:state.currentPage+1,detail:state.batchSource?.newText||''});let ok=0,fail=[];
    for(let i=0;i<edits.length;i++){
      const edit=edits[i],res=results[i]?.result||{mode:'blocked',visualVerified:false,reason:'未返回修订检查结果'},key=editKey('text',edit.page,edit.id);
      if(editModeAllowed(res)){state.edits.set(key,edit);state.feasibility.set(key,{...res,newText:edit.newText,size:edit.size,color:edit.color,x:edit.x,y:edit.y,visualAdjust:edit.visualAdjust,reusableGlyph:edit.reusableGlyph});ok++;}
      else fail.push({page:edit.page+1,reason:res.reason||'未通过修订检查'});
    }
    updateChangeCount();renderOverlays();schedulePreview(0);els.batchResult.classList.remove('hidden');els.batchResult.classList.toggle('has-fail',fail.length>0);els.batchResult.innerHTML=`<strong>批量结果：成功 ${ok} 页${fail.length?`，未修改 ${fail.length} 页`:''}${lockedMatches.length?`，锁定跳过 ${lockedMatches.length} 页`:(!fail.length?'，全部通过':'')}</strong>${fail.length?'<br>'+fail.slice(0,20).map(x=>`第 ${x.page} 页：${escapeHtml(x.reason)}`).join('<br>'):''}`;els.batchScanStatus.textContent='批量应用完成';toast(`批量修改完成：成功 ${ok} 页${fail.length?`，跳过 ${fail.length} 页`:''}${lockedMatches.length?`，锁定 ${lockedMatches.length} 页`:''}`,4200);
  }catch(e){els.batchScanStatus.textContent=`批量修改失败：${e.message}`;toast(e.message,5200);}finally{state.batchBusy=false;els.batchConfirm.disabled=false;els.batchRescan.disabled=false;}
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}


// ---------- v2.3.12 object deletion ----------
function deleteEditFromSelection(sel){
  const {type,item}=sel;
  if(type==='text')return {type:'text',action:'delete',engine:item.engine||'electronic',page:state.currentPage,id:item.id,bbox:item.bbox,tokenBbox:item.tokenBbox||item.bbox,oldText:item.text,newText:'',origin:item.origin,chars:item.chars||[],sourceText:item.sourceText||item.text};
  return {type:'image',action:'delete',page:state.currentPage,id:item.id,bbox:item.bbox,pdfBbox:item.pdfBbox||item.bbox,xref:item.xref||0,digest:item.digest||'',width:item.width||0,height:item.height||0};
}
function deleteEditFromMatch(m,type){
  const item=m.item||m;
  if(type==='text')return {type:'text',action:'delete',engine:item.engine||'electronic',page:m.page,id:item.id,bbox:item.bbox,tokenBbox:item.tokenBbox||item.bbox,oldText:item.text,newText:'',origin:item.origin,chars:item.chars||[],sourceText:item.sourceText||item.text};
  return {type:'image',action:'delete',page:m.page,id:item.id,bbox:item.bbox,pdfBbox:item.pdfBbox||item.bbox,xref:item.xref||0,digest:item.digest||'',width:item.width||0,height:item.height||0};
}
function openDeleteModal(){
  if(!state.selected)return;state.deleteMatches=[];const {type,item}=state.selected;els.deleteModalTitle.textContent=type==='text'?'删除文字':'删除图片';els.deleteModalSummary.textContent=type==='text'?`当前：${item.text||'未命名文字'}。可仅删除当前，或查找全文相同字样后选择删除。`:'可仅删除当前，或查找全文相同/高度相似图片后选择删除。';
  els.deleteSourceCard.innerHTML=type==='text'?`<strong>${escapeHtml(item.text||'')}</strong><small>第 ${state.currentPage+1} 页 · 当前选中文字</small>`:`<strong>当前图片</strong><small>第 ${state.currentPage+1} 页 · ${item.width||'?'} × ${item.height||'?'} px</small>`;
  els.deleteStatus.textContent='默认只删除当前选中对象。点击“查找相同项”可批量预览。';els.deleteMatchGrid.innerHTML='';els.deleteRange.value='';els.deleteConfirm.textContent='删除当前';els.deleteModal.classList.remove('hidden');
}
function closeDeleteModal(){els.deleteModal.classList.add('hidden');}
function renderDeleteMatches(){
  const type=state.selected?.type;if(!type)return;els.deleteMatchGrid.innerHTML='';
  if(!state.deleteMatches.length){els.deleteStatus.textContent='没有找到其他匹配项。';return;}
  for(const [i,m] of state.deleteMatches.entries()){
    const row=document.createElement('label');row.className='delete-match-row';const text=type==='text'?(m.item?.text||'文字'):`图片 ${m.item?.width||'?'}×${m.item?.height||'?'}`;const score=type==='image'&&Number.isFinite(+m.similarity)?` · 相似度 ${Math.round(+m.similarity)}%`:'';
    row.innerHTML=`<input type="checkbox" data-delete-index="${i}" data-page="${m.page+1}" checked><span><strong>第 ${m.page+1} 页</strong><small>${escapeHtml(text)}${score}</small></span>`;els.deleteMatchGrid.appendChild(row);
  }
  els.deleteStatus.textContent=`找到 ${state.deleteMatches.length} 个匹配项。请取消不需要删除的项目后再执行。`;els.deleteConfirm.textContent='删除选中项';
}
async function findDeleteMatches(){
  if(state.deleteBusy||!state.selected)return;state.deleteBusy=true;els.deleteFindMatches.disabled=true;els.deleteStatus.textContent='正在查找相同项…';
  try{const source=state.selected.type==='text'?buildTextEdit(state.selected.item):state.selected.item;const r=await fetch('/api/delete/matches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,type:state.selected.type,source})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();state.deleteMatches=(j.matches||[]);renderDeleteMatches();}catch(e){els.deleteStatus.textContent=`查找失败：${e.message}`;toast(e.message,5200);}finally{state.deleteBusy=false;els.deleteFindMatches.disabled=false;}
}
function applyDeleteRange(){const set=parsePageRange(els.deleteRange.value,state.pageCount);if(!set.size)return toast('没有识别到有效页码，例如：1-5,8,12-20');document.querySelectorAll('[data-delete-index]').forEach(x=>{x.checked=set.has(+x.dataset.page);});toast(`已按页范围选择 ${[...document.querySelectorAll('[data-delete-index]')].filter(x=>x.checked).length} 项`);}
async function commitDeleteEdits(currentOnly=false){
  if(state.deleteBusy||!state.selected)return;let edits=[];
  if(currentOnly||!state.deleteMatches.length)edits=[deleteEditFromSelection(state.selected)];else edits=[...document.querySelectorAll('[data-delete-index]:checked')].map(x=>deleteEditFromMatch(state.deleteMatches[+x.dataset.deleteIndex],state.selected.type));
  if(!edits.length)return toast('没有选择要删除的项目');
  const before=snapshot();
  state.deleteBusy=true;
  els.deleteConfirm.disabled=true;
  if(els.deleteCurrentOnly)els.deleteCurrentOnly.disabled=true;
  if(els.deleteFindMatches)els.deleteFindMatches.disabled=true;
  els.deleteStatus.textContent=`正在生成删除预览：${edits.length} 项…`;
  beginPageProgress(`正在生成删除预览：${edits.length} 项…`);
  try{
    pushHistory(`${currentOnly?'删除当前':'批量删除'} ${edits.length} 项`,{page:state.currentPage+1,detail:state.selected?.type==='text'?(state.selected.item?.text||'文字'):'图片'});
    for(const e of edits)state.edits.set(editKey(e.type,e.page,e.id),e);
    updateChangeCount();renderOverlays();
    // v2.3.13: 删除确认后立即退出模态框，让全局进度层可见；删除渲染继续在后台执行。
    closeDeleteModal();
    toast(`正在处理 ${edits.length} 项删除，请等待预览更新…`,2600);
    await refreshPreview();
    toast(`已生成删除预览：${edits.length} 项`,3600);
    showSelectedProps();
  }catch(e){
    // 删除预览失败时恢复操作前状态，避免页面留下半完成删除记录。
    restoreSnapshot(before);
    toast(`删除预览失败，已恢复原状态：${e.message}`,6200);
  }finally{
    endPageProgress();state.deleteBusy=false;els.deleteConfirm.disabled=false;
    if(els.deleteCurrentOnly)els.deleteCurrentOnly.disabled=false;
    if(els.deleteFindMatches)els.deleteFindMatches.disabled=false;
  }
}

// ---------- events ----------
els.importBtn.onclick=els.welcomeImport.onclick=()=>els.fileInput.click();els.fileInput.onchange=e=>{importPdf(e.target.files[0]);e.target.value='';};els.exportBtn.onclick=exportPdf;if(els.changeLogBtn)els.changeLogBtn.onclick=()=>openChangeLog(false);
els.prevPage.onclick=()=>loadPage(state.currentPage-1);els.nextPage.onclick=()=>loadPage(state.currentPage+1);
els.zoomIn.onclick=()=>restoreCustomZoom(state.zoom+.1);els.zoomOut.onclick=()=>restoreCustomZoom(state.zoom-.1);
els.fitWidth.onclick=fitWidth;els.fitPage.onclick=fitPage;
els.editLine.onclick=()=>{const item=state.selected?.item;if(!item)return;const line=state.pageData.text.find(x=>x.id===(item.lineId||item.id));if(line)selectObject('text',line,editKey('text',state.currentPage,line.id));};
els.cleanPreview.onclick=()=>{state.cleanPreview=!state.cleanPreview;els.cleanPreview.classList.toggle('active',state.cleanPreview);els.cleanPreview.textContent=state.cleanPreview?'退出':'净图';if(state.cleanPreview)clearProps();renderOverlays();toast(state.cleanPreview?'已隐藏编辑辅助框，显示当前 PDF 页面':'已返回编辑模式');};
els.selectionMode.onchange=()=>{state.selectionMode=els.selectionMode.value;state.cycleSig='';renderOverlays();if(state.selectionMode==='text')toast('只选文字：图片不会拦截点击，隐藏在图片下面的文字也可选');else if(state.selectionMode==='image')toast('只选图片：文字点击已暂时穿透');else if(state.selectionMode==='manual')toast('框选字段：在 PDF 页面拖动以局部 OCR 识别字段；Esc 可取消。');else toast('智能选择：优先文字；Alt+单击可循环重叠对象');};

[els.textContent,els.fontSize,els.fontColor,els.textX,els.textY].forEach(el=>el.addEventListener('input',()=>{updateFinalGlyphPreview();updatePrecisionMode();markRunPending();}));
const scanTuneInputs=[els.scanSizeScale,els.scanWidthScale,els.scanXOffset,els.scanYOffset,els.scanDarkness,els.scanStroke,els.scanClarity,els.scanCleanup,els.scanEdgeBlend].filter(Boolean);
scanTuneInputs.forEach(el=>el.addEventListener('input',()=>{renderScanTuneValues();if(state.selected?.item?.engine==='scan'){updatePrecisionMode();markRunPending();}}));
Object.entries(SCAN_TUNE_META).forEach(([id,meta])=>{const input=els[meta.inputId];if(!input)return;const commit=()=>applyTuneNumberInput(id,true);input.addEventListener('change',commit);input.addEventListener('blur',commit);input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commit();}});});
if(els.scanFontChoice)els.scanFontChoice.addEventListener('change',()=>{if(state.selected?.item?.engine==='scan'){updateFinalGlyphPreview();updatePrecisionMode();markRunPending();}});
if(els.scanTuneSection)els.scanTuneSection.addEventListener('click',e=>{const b=e.target.closest('[data-tune-reset]');if(b){e.preventDefault();resetOneScanTune(b.dataset.tuneReset);}});if(els.scanTuneCopy)els.scanTuneCopy.onclick=copyScanTuneParams;if(els.scanTunePaste)els.scanTunePaste.onclick=pasteScanTuneParams;if(els.copyFinishedGlyph)els.copyFinishedGlyph.onclick=copyFinishedGlyph;if(els.pasteFinishedGlyph)els.pasteFinishedGlyph.onclick=pasteFinishedGlyph;if(els.finishedGlyphMode)els.finishedGlyphMode.onchange=()=>{if(state.glyphClipboard){state.glyphClipboard.mode=els.finishedGlyphMode.value;state.glyphClipboard.asset={...state.glyphClipboard.asset,mode:els.finishedGlyphMode.value};state.glyphLibrary.set(state.glyphClipboard.char,state.glyphClipboard);renderFinishedGlyphLibrary();}};
if(els.applyScanTune)els.applyScanTune.onclick=async()=>{if(state.selected?.item?.engine!=='scan'||state.runBusy)return;els.applyScanTune.disabled=true;beginPageProgress('正在应用视觉微调…');try{await runSelectedEdit();}finally{endPageProgress();els.applyScanTune.disabled=false;}};
if(els.runEditBtn)els.runEditBtn.onclick=runSelectedEdit;
els.resetTextBtn.onclick=()=>resetSelected('text');els.batchApplyBtn.onclick=openBatchModal;els.imageInput.onchange=e=>{commitImage(e.target.files[0]);e.target.value='';};if(els.deleteTextBtn)els.deleteTextBtn.onclick=openDeleteModal;if(els.deleteImageBtn)els.deleteImageBtn.onclick=openDeleteModal;if(els.deleteModalClose)els.deleteModalClose.onclick=closeDeleteModal;if(els.deleteCancel)els.deleteCancel.onclick=closeDeleteModal;if(els.deleteModal)els.deleteModal.onclick=e=>{if(e.target===els.deleteModal)closeDeleteModal();};if(els.deleteCurrentOnly)els.deleteCurrentOnly.onclick=()=>commitDeleteEdits(true);if(els.deleteFindMatches)els.deleteFindMatches.onclick=findDeleteMatches;if(els.deleteRangeApply)els.deleteRangeApply.onclick=applyDeleteRange;if(els.deleteConfirm)els.deleteConfirm.onclick=()=>commitDeleteEdits(false);
els.imageFit.onchange=()=>{if(state.selected?.type!=='image')return;const e=state.edits.get(state.selected.key);if(!e)return;pushHistory('调整图片适应方式',{page:state.currentPage+1,detail:els.imageFit.value});e.fit=els.imageFit.value;state.edits.set(state.selected.key,e);updateChangeCount();schedulePreview();};els.resetImageBtn.onclick=()=>resetSelected('image');
els.undoBtn.onclick=()=>{if(!state.undo.length)return;state.redo.push(snapshot());restoreSnapshot(state.undo.pop());toast('已撤销一步；可在修改历史中直接返回任意节点');};els.redoBtn.onclick=()=>{if(!state.redo.length)return;state.undo.push(snapshot());restoreSnapshot(state.redo.pop());toast('已重做一步');};if(els.historyBtn)els.historyBtn.onclick=openVersionHistory;if(els.historyClose)els.historyClose.onclick=closeVersionHistory;if(els.historyCancel)els.historyCancel.onclick=closeVersionHistory;if(els.historyRestore)els.historyRestore.onclick=restoreHistoryVersion;if(els.historyRename)els.historyRename.onclick=renameHistoryVersion;if(els.historyModal)els.historyModal.onclick=e=>{if(e.target===els.historyModal)closeVersionHistory();};
// v1.7.1: central hit-test. Visual overlay rectangles NEVER decide what is selected.
// This keeps the v1.6 engine behavior deterministic even when a large image overlaps text.
function manualPoint(e){const r=els.pageWrap.getBoundingClientRect();return [(e.clientX-r.left)/(state.zoom*state.scale),(e.clientY-r.top)/(state.zoom*state.scale)];}
function drawManualRect(rect){let el=els.overlayLayer.querySelector('.manual-selection');if(!el){el=document.createElement('div');el.className='manual-selection';els.overlayLayer.appendChild(el);}const [x0,y0,x1,y1]=rect;Object.assign(el.style,{left:`${toPx(x0)}px`,top:`${toPx(y0)}px`,width:`${toPx(x1-x0)}px`,height:`${toPx(y1-y0)}px`});}
function clearManualRect(){state.manualSelectionRect=null;els.overlayLayer.querySelector('.manual-selection')?.remove();}
async function completeManualSelection(){const rect=state.manualSelectionRect;if(!rect||rect[2]-rect[0]<4||rect[3]-rect[1]<4){clearManualRect();return;}showLoading(true);try{const r=await fetch('/api/manual-region',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,bbox:rect})});if(!r.ok)throw new Error(await apiError(r));const f=(await r.json()).field;const item={id:`manual-${Date.now()}`,engine:'scan',text:f.text,bbox:f.bbox,tokenBbox:f.bbox,origin:[f.bbox[0],f.bbox[3]],chars:f.chars||[],size:Math.max(7,f.bbox[3]-f.bbox[1]),color:'#000000',font:'扫描 OCR 修订',manualSelection:true,sourceText:'手动框选区域'};clearManualRect();selectObject('text',item,editKey('text',state.currentPage,item.id));}catch(err){clearManualRect();toast(err.message,5200);}finally{showLoading(false);}}
els.pageWrap.onmousedown=e=>{if(state.cleanPreview||e.button!==0)return;const p=manualPoint(e);if(state.pageNumberBoxSlot){state.pageNumberBoxSelecting=true;state.pageNumberBoxRect=[p[0],p[1],p[0],p[1]];drawPageNumberBoxRect(state.pageNumberBoxRect);e.preventDefault();return;}if(state.selectionMode!=='manual')return;state.manualSelecting=true;state.manualSelectionRect=[p[0],p[1],p[0],p[1]];drawManualRect(state.manualSelectionRect);e.preventDefault();};
window.addEventListener('mousemove',e=>{if(state.pageNumberBoxSelecting){const p=manualPoint(e),r=state.pageNumberBoxRect;state.pageNumberBoxRect=[Math.min(r[0],p[0]),Math.min(r[1],p[1]),Math.max(r[0],p[0]),Math.max(r[1],p[1])];drawPageNumberBoxRect(state.pageNumberBoxRect);return;}if(!state.manualSelecting)return;const p=manualPoint(e),r=state.manualSelectionRect;state.manualSelectionRect=[Math.min(r[0],p[0]),Math.min(r[1],p[1]),Math.max(r[0],p[0]),Math.max(r[1],p[1])];drawManualRect(state.manualSelectionRect);});
window.addEventListener('mouseup',e=>{if(state.pageNumberBoxSelecting){state.pageNumberBoxSelecting=false;state.suppressNextClick=true;completePageNumberBoxSelection();return;}if(!state.manualSelecting)return;state.manualSelecting=false;state.suppressNextClick=true;completeManualSelection();});
els.pageWrap.onclick=(e)=>{if(state.cleanPreview)return;const c=candidatesAtEvent(e);if(state.pageNumberBoxSlot||state.suppressNextClick){state.suppressNextClick=false;return;}if(state.selectionMode==='manual'){return;}if(c.length)selectAtPoint(e);else{clearProps();renderOverlays();}};

els.batchClose.onclick=closeBatchModal;els.batchModal.onclick=e=>{if(e.target===els.batchModal)closeBatchModal();};els.batchSamePosition.onchange=scanBatchMatches;els.batchRescan.onclick=scanBatchMatches;els.batchSelectAll.onclick=()=>setBatchSelection('all');els.batchSelectNone.onclick=()=>setBatchSelection('none');els.batchInvert.onclick=()=>setBatchSelection('invert');els.batchRangeApply.onclick=applyRangeSelection;els.batchConfirm.onclick=applyBatchEdits;
if(els.changeLogClose)els.changeLogClose.onclick=closeChangeLog;if(els.changeLogCancel)els.changeLogCancel.onclick=closeChangeLog;if(els.changeLogConfirm)els.changeLogConfirm.onclick=performExportPdf;if(els.changeLogModal)els.changeLogModal.onclick=e=>{if(e.target===els.changeLogModal)closeChangeLog();};

// ---------- v2.3.19 box-selected, per-page anchored batch page-number editor ----------
const PAGE_NUMBER_PRESETS=Object.freeze({
  current:'{current}',current_total_slash:'{current}/{total}',current_total_cn:'第{current}页，共{total}页',total:'{total}'
});
const PAGE_NUMBER_ROLE_LABELS=Object.freeze({current:'当前页',total:'总页数',pdfpage:'PDF页'});
function pageNumberSlotEls(slot){return slot==='B'?{use:els.pageNumberUseB,clear:els.pageNumberClearB,state:els.pageNumberSlotBState,format:els.pageNumberFormatB,custom:els.pageNumberCustomB}:{use:els.pageNumberUseA,clear:els.pageNumberClearA,state:els.pageNumberSlotAState,format:els.pageNumberFormatA,custom:els.pageNumberCustomA};}
function inferPageNumberTemplate(text){
  text=String(text||'').trim();const groups=[...text.matchAll(/\d+/g)];if(!groups.length)return {preset:'current',format:'{current}'};
  if(groups.length>=2){let out=text,offset=0;for(const [i,g] of groups.slice(0,2).entries()){const role=i===0?'{current}':'{total}',a=g.index+offset,b=a+g[0].length;out=out.slice(0,a)+role+out.slice(b);offset+=role.length-g[0].length;}const compact=out.replace(/\s+/g,'');if(compact==='{current}/{total}'||compact==='{current}／{total}')return {preset:'current_total_slash',format:out};if(/^第\{current\}页[，,]?共\{total\}页$/.test(compact))return {preset:'current_total_cn',format:out};return {preset:'custom',format:out};}
  const g=groups[0],before=text.slice(0,g.index),after=text.slice(g.index+g[0].length),totalHint=/(?:共|总|合计|of\s*$|total\s*$)/i.test(before),role=totalHint?'{total}':'{current}',out=before+role+after;
  if(/^\s*\d+\s*$/.test(text))return totalHint?{preset:'total',format:'{total}'}:{preset:'current',format:'{current}'};
  return {preset:'custom',format:out};
}
function pageNumberRoles(fmt){return [...String(fmt||'').matchAll(/\{(current|total|pdfpage)\}/g)].map(m=>m[1]);}
function formatPageNumber(fmt,{current,total,pdfpage}){return String(fmt||'{current}').replace(/\{current\}/g,String(current)).replace(/\{total\}/g,String(total)).replace(/\{pdfpage\}/g,String(pdfpage));}
function pageNumberRoleSummary(template){const groups=template?.numberGroups||[],roles=pageNumberRoles(template?.format||'{current}');if(!groups.length)return '';return groups.slice(0,Math.max(1,roles.length)).map((g,i)=>`${PAGE_NUMBER_ROLE_LABELS[roles[i]||'current']||'数字'} ${g.text||'—'}`).join(' · ');}
function makePageNumberBoxTemplate(slot,field,selectionBbox,pageMeta={},base={}){
  const selection=(selectionBbox||field?.selectionBbox||field?.bbox||[]).map(Number);if(selection.length!==4)return null;const text=String(field?.text||'').trim(),inferred=inferPageNumberTemplate(text),actual=(field?.bbox||selection).map(Number),origin=field?.origin||[actual[0],actual[3]],engine=field?.engine||((pageMeta.pageKind||state.pageData?.pageKind)==='scan'?'scan':'electronic');
  const visualAdjust=engine==='scan'?normalizeScanVisualAdjust(base.visualAdjust):undefined;
  const ox=Number(origin?.[0]??actual[0])-selection[0],oy=Number(origin?.[1]??actual[3])-selection[1],global=pageNumberRange(),ui=pageNumberSlotEls(slot);
  const applyFrom=Math.max(global.from,Math.min(global.to,Number(base.applyFrom||ui.rangeFrom?.value||global.from))),applyTo=Math.max(applyFrom,Math.min(global.to,Number(base.applyTo||ui.rangeTo?.value||global.to)));
  return {...base,slot,sourcePage:state.currentPage,sourceId:field?.id||`box-${slot}-${Date.now()}`,sourceText:text,sourceActualBbox:actual,bbox:selection,pageWidth:Number(pageMeta.pageWidth||state.pageData?.width)||1,pageHeight:Number(pageMeta.pageHeight||state.pageData?.height)||1,engine,font:field?.font||base.font||'',size:Number(field?.size)||base.size||Math.max(6,actual[3]-actual[1]),color:field?.color||base.color||'#000000',alpha:field?.alpha??base.alpha??255,rotation:field?.rotation||base.rotation||0,originOffsetX:ox,originOffsetY:oy,visualAdjust,format:base.format||inferred.format,preset:base.preset||inferred.preset,numberGroups:field?.numberGroups||[],captureMode:'box',applyFrom,applyTo,allowBlankAdd:base.allowBlankAdd??!!ui.allowAdd?.checked};
}
function storePageNumberBoxTemplate(slot,field,selectionBbox,pageMeta={}){
  const template=makePageNumberBoxTemplate(slot,field,selectionBbox,pageMeta,state.pageNumberTemplates[slot]||{});if(!template)return false;state.pageNumberTemplates[slot]=template;
  const ui=pageNumberSlotEls(slot);if(ui.format)ui.format.value=template.preset;if(ui.custom)ui.custom.value=template.format;if(ui.rangeFrom)ui.rangeFrom.value=template.applyFrom;if(ui.rangeTo)ui.rangeTo.value=template.applyTo;if(ui.allowAdd)ui.allowAdd.checked=!!template.allowBlankAdd;renderPageNumberTemplateSlots();invalidatePageNumberScan('页码框选模板已更新，请重新扫描。');return true;
}
function drawPageNumberBoxRect(rect){let el=els.overlayLayer.querySelector('.page-number-box-selection');if(!el){el=document.createElement('div');el.className='page-number-box-selection';els.overlayLayer.appendChild(el);}const [x0,y0,x1,y1]=rect;Object.assign(el.style,{left:`${toPx(x0)}px`,top:`${toPx(y0)}px`,width:`${Math.max(1,toPx(x1-x0))}px`,height:`${Math.max(1,toPx(y1-y0))}px`});}
function clearPageNumberBoxRect(){state.pageNumberBoxRect=null;state.pageNumberBoxSelecting=false;els.overlayLayer.querySelector('.page-number-box-selection')?.remove();}
function cancelPageNumberBoxSelect({reopen=false}={}){state.pageNumberBoxSlot=null;state.pageNumberBoxTarget=null;clearPageNumberBoxRect();document.body.classList.remove('page-number-box-mode');if(reopen)openPageNumberModal();}
function beginPageNumberBoxSelect(slot,opts={}){if(!state.id||state.pageNumberBusy)return;state.pageNumberBoxSlot=slot;state.pageNumberBoxTarget=opts?.override?{page:Number(opts.page),slot,override:true}:null;clearPageNumberBoxRect();document.body.classList.add('page-number-box-mode');els.pageNumberModal?.classList.add('hidden');toast(opts?.override?`重新定位 PDF 第 ${Number(opts.page)+1} 页 · 位置 ${slot}：请拖框圈住真实页码`:`框选页码位置 ${slot}：请在当前 PDF 页面拖出只包含页码的矩形区域`,5200);}
async function reboxPageNumberResult(page,slot){if(state.pageNumberBusy)return;closePageNumberModal();if(state.currentPage!==page)await loadPage(page);beginPageNumberBoxSelect(slot,{override:true,page});}
async function completePageNumberBoxSelection(){const slot=state.pageNumberBoxSlot,raw=state.pageNumberBoxRect,target=state.pageNumberBoxTarget;if(!slot||!raw)return;const w=Number(state.pageData?.width)||1,h=Number(state.pageData?.height)||1,rect=[Math.max(0,Math.min(w,raw[0])),Math.max(0,Math.min(h,raw[1])),Math.max(0,Math.min(w,raw[2])),Math.max(0,Math.min(h,raw[3]))];if(rect[2]-rect[0]<4||rect[3]-rect[1]<4){cancelPageNumberBoxSelect({reopen:true});return toast('框选区域太小，请重新框选页码');}
  showLoading(true);try{const r=await fetch('/api/page-number-template/capture',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,bbox:rect})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json(),field=j.field||{},groups=field.numberGroups||[];if(target?.override){const base=state.pageNumberTemplates[slot];if(!base)throw new Error(`位置 ${slot} 的主模板不存在`);const override=makePageNumberBoxTemplate(slot,field,rect,j,{...base,applyFrom:state.currentPage+1,applyTo:state.currentPage+1});state.pageNumberPageOverrides[`${state.currentPage}:${slot}`]=override;invalidatePageNumberScan(`PDF 第 ${state.currentPage+1} 页 · 位置 ${slot} 已人工重新定位，请重新扫描。`);toast(groups.length?`已重新定位：${String(field.text||'').trim()}`:`已保存该页人工位置，但框内未识别到数字`,5200);}else{storePageNumberBoxTemplate(slot,field,rect,j);toast(groups.length?`位置 ${slot} 已识别：${String(field.text||'').trim()}`:`位置 ${slot} 已保存，但当前框内未识别到数字；默认不会自动新增，可在模板中单独开启`,5200);}}catch(err){toast(`页码框选识别失败：${err.message}`,6200);}finally{showLoading(false);state.pageNumberBoxSlot=null;state.pageNumberBoxTarget=null;clearPageNumberBoxRect();document.body.classList.remove('page-number-box-mode');openPageNumberModal();}}
function clearPageNumberTemplate(slot){state.pageNumberTemplates[slot]=null;for(const k of Object.keys(state.pageNumberPageOverrides))if(k.endsWith(`:${slot}`))delete state.pageNumberPageOverrides[k];renderPageNumberTemplateSlots();invalidatePageNumberScan('页码位置模板已变化，请重新扫描。');}
function renderPageNumberTemplateSlots(){for(const slot of ['A','B']){const t=state.pageNumberTemplates[slot],ui=pageNumberSlotEls(slot);if(!ui.state)continue;if(t){const roles=pageNumberRoleSummary(t);ui.state.innerHTML=`<strong>已框选 · PDF 第 ${t.sourcePage+1} 页</strong><span>${escapeHtml(t.sourceText||'当前页为空白区域')} · ${t.engine==='scan'?'扫描页':'电子页'}</span>${roles?`<em>${escapeHtml(roles)}</em>`:'<em>未识别到数字，可手动选择显示格式</em>'}`;if(ui.format&&document.activeElement!==ui.format)ui.format.value=t.preset||'custom';if(ui.custom&&document.activeElement!==ui.custom)ui.custom.value=t.format||'{current}';ui.clear.disabled=false;}else{ui.state.innerHTML='<span>未设置 · 点击“框选位置”后在页面拖框</span>';if(ui.format)ui.format.value='current';if(ui.custom)ui.custom.value='{current}';ui.clear.disabled=true;}ui.use.disabled=!state.id;}}
function currentPageNumberFormat(slot){const t=state.pageNumberTemplates[slot],ui=pageNumberSlotEls(slot);if(!t)return '';const value=String(ui.custom?.value||t.format||'{current}').trim();return value||'{current}';}
function pageNumberRange(){const from=Math.max(1,Math.min(state.pageCount,+els.pageNumberFrom.value||1)),to=Math.max(from,Math.min(state.pageCount,+els.pageNumberTo.value||from));els.pageNumberFrom.value=from;els.pageNumberTo.value=to;return {from,to};}
function pageNumberTotal(){const {from,to}=pageNumberRange(),mode=els.pageNumberTotalMode?.value||'range';let total=to-from+1;if(mode==='pdf')total=state.pageCount;else if(mode==='manual')total=Math.max(1,+els.pageNumberTotalValue.value||1);if(els.pageNumberTotalValue){els.pageNumberTotalValue.disabled=mode!=='manual';els.pageNumberTotalValue.value=total;}return total;}
function updatePageNumberSummary(){if(!els.pageNumberFrom)return;const {from,to}=pageNumberRange(),start=+els.pageNumberStart.value||1,end=start+(to-from);els.pageNumberEnd.value=end;const total=pageNumberTotal();const active=['A','B'].filter(s=>state.pageNumberTemplates[s]);const previews=active.map(slot=>{const fmt=currentPageNumberFormat(slot),first=formatPageNumber(fmt,{current:start,total,pdfpage:from}),last=formatPageNumber(fmt,{current:end,total,pdfpage:to});return `${slot}：${first}${from===to?'':` → ${last}`}`;});els.pageNumberPreviewSummary.textContent=`PDF 第 ${from}-${to} 页 · 编号 ${start}-${end} · 总页数 ${total}${previews.length?' · '+previews.join('；'):''}`;}
function invalidatePageNumberScan(message='设置已变化，请重新扫描模板位置。'){state.pageNumberScanResults=[];state.pageNumberMatches=[];if(els.pageNumberResults)els.pageNumberResults.innerHTML='';if(els.pageNumberApply)els.pageNumberApply.disabled=true;if(els.pageNumberStatus)els.pageNumberStatus.textContent=message;updatePageNumberSummary();}
function applyPageNumberPreset(slot){const ui=pageNumberSlotEls(slot),t=state.pageNumberTemplates[slot];if(!ui.format||!ui.custom)return;if(ui.format.value!=='custom')ui.custom.value=PAGE_NUMBER_PRESETS[ui.format.value]||'{current}';if(t){t.preset=ui.format.value;t.format=ui.custom.value;}invalidatePageNumberScan();renderPageNumberTemplateSlots();}
function updatePageNumberCustom(slot){const ui=pageNumberSlotEls(slot),t=state.pageNumberTemplates[slot];if(!t)return;t.format=String(ui.custom.value||'').trim()||'{current}';const preset=Object.entries(PAGE_NUMBER_PRESETS).find(([,v])=>v===t.format)?.[0]||'custom';t.preset=preset;ui.format.value=preset;invalidatePageNumberScan();renderPageNumberTemplateSlots();}
function activePageNumberTemplates(){const out=[];for(const slot of ['A','B']){const t=state.pageNumberTemplates[slot];if(!t)continue;const format=currentPageNumberFormat(slot);if(!pageNumberRoles(format).length)continue;out.push({...t,format});}return out;}
function openPageNumberModal(){if(!state.id)return;els.pageNumberFrom.max=state.pageCount;els.pageNumberTo.max=state.pageCount;if(!activePageNumberTemplates().length&&!state.pageNumberScanResults.length){els.pageNumberFrom.value=state.currentPage+1;els.pageNumberTo.value=state.pageCount;els.pageNumberStart.value=1;}else els.pageNumberTo.value=Math.min(state.pageCount,+els.pageNumberTo.value||state.pageCount);renderPageNumberTemplateSlots();updatePageNumberSummary();if(!activePageNumberTemplates().length)els.pageNumberStatus.textContent='请点击“框选位置 A / B”，然后在 PDF 页面直接拖框。';else if(!state.pageNumberScanResults.length)els.pageNumberStatus.textContent='框选模板已设置。确认范围和格式后，点击“扫描框选位置”。';els.pageNumberApply.disabled=!state.pageNumberScanResults.length;els.pageNumberModal.classList.remove('hidden');}
function closePageNumberModal(){if(state.pageNumberBusy)return;els.pageNumberModal.classList.add('hidden');}
function numericSkeleton(text){return String(text||'').replace(/\d+/g,'{#}').replace(/\s+/g,'').toLowerCase();}
function formatSkeleton(fmt){return String(fmt||'').replace(/\{(?:current|total|pdfpage)\}/g,'{#}').replace(/\s+/g,'').toLowerCase();}
function pageNumberLiteralText(fmt){return String(fmt||'').replace(/\{(?:current|total|pdfpage)\}/g,'').replace(/\s+/g,'');}
function bboxOverlapRatio(a,b){if(!a||!b||a.length!==4||b.length!==4)return 0;const ax0=+a[0],ay0=+a[1],ax1=+a[2],ay1=+a[3],bx0=+b[0],by0=+b[1],bx1=+b[2],by1=+b[3],iw=Math.max(0,Math.min(ax1,bx1)-Math.max(ax0,bx0)),ih=Math.max(0,Math.min(ay1,by1)-Math.max(ay0,by0)),ia=iw*ih,aa=Math.max(1,(ax1-ax0)*(ay1-ay0)),ba=Math.max(1,(bx1-bx0)*(by1-by0));return ia/Math.min(aa,ba);}
function pageNumberTemplateConflict(templates){if((templates||[]).length<2)return null;const a=templates[0],b=templates[1],ratio=bboxOverlapRatio(a.bbox,b.bbox);return ratio>.30?`位置 ${a.slot} 与 ${b.slot} 的框选区域重叠 ${Math.round(ratio*100)}%，请重新框选，避免同一页码被重复写入。`:null;}
function pageNumberValuesForPage(page){const {from}=pageNumberRange(),start=+els.pageNumberStart.value||1,total=pageNumberTotal();return {current:start+(page+1-from),total,pdfpage:page+1};}
function pageNumberTemplateSourceMap(t){const roles=pageNumberRoles(t?.format||'{current}'),groups=t?.numberGroups||[],out={};roles.forEach((role,i)=>{const n=Number(String(groups[i]?.text||'').replace(/\D/g,''));if(Number.isFinite(n)&&String(groups[i]?.text||'').match(/\d/))out[role]=n;});return out;}
function validatePageNumberSlot(sr,t,page){
  if(!t)return null;
  if(!sr.found){
    return t.allowBlankAdd?null:{kind:'fail',code:'not-found',text:'未识别到原页码；不会新增。请对此页重新框选或手动接管。'};
  }
  // v2.3.24: OCR only locates the existing page-number digits. It must not
  // decide what the new page number should be, and sequence mismatches must
  // never block a valid existing-number replacement.
  const roles=pageNumberRoles(t.format),parts=sr.parts||[],problems=[];
  if(roles.length&&parts.length<roles.length){
    const old=String(sr.oldText||sr.item?.text||'');
    if(pageNumberLiteralText(t.format)||/\D/.test(old))problems.push('未可靠定位页码中的数字子区域');
  }
  return problems.length?{kind:'fail',code:'geometry',text:problems.join('；')}:null;
}
function pageNumberRecognitionWarning(sr,t,page){
  if(!sr?.found||!t)return null;
  // OCR only supplies location. Do not compare the original printed number with
  // PDF index, template sequence, or the requested target value: covers,
  // unnumbered pages and section restarts make those relations legitimately differ.
  const roles=pageNumberRoles(t.format),parts=sr.parts||[],notes=[];
  for(let i=0;i<Math.min(roles.length,parts.length);i++){
    const raw=String(parts[i].oldText||'');
    if(raw&&!/^\d+$/.test(raw))notes.push(`数字识别文本“${raw}”需检查`);
  }
  return notes.length?notes.join('；'):null;
}
function annotatePageNumberAnomalies(){const templates=new Map(activePageNumberTemplates().map(t=>[t.slot,t]));let count=0;for(const r of state.pageNumberScanResults){for(const sr of r.slots||[]){const t=templates.get(sr.slot);sr.validation=validatePageNumberSlot(sr,t,r.page);sr.warning=pageNumberRecognitionWarning(sr,t,r.page);if(sr.validation)count++;}}return count;}
function pageNumberResultIsBad(sr){return !!(sr?.validation||sr?.runStatus?.kind==='fail');}
function renderPageNumberResults(){
  els.pageNumberResults.innerHTML='';if(!state.pageNumberScanResults.length)return;const templates=new Map(activePageNumberTemplates().map(t=>[t.slot,t]));
  for(const r of state.pageNumberScanResults){const vals=pageNumberValuesForPage(r.page),row=document.createElement('div');row.className='page-number-row-v2';row.dataset.page=String(r.page);const slotHtml=(r.slots||[]).map(sr=>{const t=templates.get(sr.slot);if(!t)return '';const target=formatPageNumber(t.format,vals),status=sr.runStatus||'',roles=pageNumberRoles(t.format),parts=sr.parts||[];let desc='';if(sr.validation){desc=`<b class="pn-anomaly-text">异常：${escapeHtml(sr.validation.text)}</b>`;}else if(sr.found&&parts.length>=roles.length&&roles.length){const changes=parts.slice(0,roles.length).map((part,i)=>`${escapeHtml(part.oldText||'')}→${escapeHtml(String(rolePageNumberValue(part.role||roles[i],vals)))}`).join('；');desc=`数字原位 <b>${changes}</b> <small>固定文字保留</small>`;}else if(sr.found)desc=`替换 <b>${escapeHtml(sr.oldText||'')}</b> → <b>${escapeHtml(target)}</b>`;else if(t.allowBlankAdd)desc=`新增 <b>${escapeHtml(target)}</b>`;else desc='<b class="pn-anomaly-text">未识别原页码，默认不新增</b>';if(sr.warning&&!sr.validation)desc+=`<em class="pn-run skip">${escapeHtml(sr.warning)}</em>`;if(status)desc+=`<em class="pn-run ${status.kind||''}">${escapeHtml(status.text||'')}</em>`;const generated=allEdits().some(e=>e.page===r.page&&e.pageNumberSlot===sr.slot);return `<span class="pn-slot-result ${sr.found?'replace':'add'} ${pageNumberResultIsBad(sr)?'anomaly':''}"><i>${sr.slot}</i><span class="pn-desc">${desc}</span><span class="pn-result-actions"><button type="button" class="mini-btn soft-btn pn-rebox" data-page="${r.page}" data-slot="${escapeHtml(sr.slot)}">此页重定位</button>${generated?`<button type="button" class="mini-btn soft-btn danger pn-delete-group" data-page="${r.page}" data-slot="${escapeHtml(sr.slot)}">删除此页此组</button>`:''}</span></span>`;}).join('');row.innerHTML=`<strong>PDF 第 ${r.page+1} 页</strong><div>${slotHtml}</div>`;els.pageNumberResults.appendChild(row);}
  els.pageNumberResults.querySelectorAll('.pn-rebox').forEach(b=>b.onclick=()=>reboxPageNumberResult(+b.dataset.page,b.dataset.slot));els.pageNumberResults.querySelectorAll('.pn-delete-group').forEach(b=>b.onclick=()=>deletePageNumberGroup(+b.dataset.page,b.dataset.slot));
}
async function scanPageNumbers(){
  if(state.pageNumberBusy)return;const templates=activePageNumberTemplates();if(!templates.length)return toast('请先框选至少一个页码位置，并确保模板包含 {current}、{total} 或 {pdfpage}');const conflict=pageNumberTemplateConflict(templates);if(conflict){els.pageNumberStatus.textContent=conflict;return toast(conflict,6200);}const {from,to}=pageNumberRange();state.pageNumberBusy=true;els.pageNumberScan.disabled=true;els.pageNumberApply.disabled=true;els.pageNumberStatus.textContent=`正在按框选位置扫描 PDF 第 ${from}-${to} 页…`;
  const payloadTemplates=templates.map(t=>({slot:t.slot,bbox:t.bbox,pageWidth:t.pageWidth,pageHeight:t.pageHeight,engine:t.engine,format:t.format,sourceText:t.sourceText,sourceId:t.sourceId,captureMode:t.captureMode||'box',sourceGroupCount:(t.numberGroups||[]).length,applyFrom:t.from-1,applyTo:t.to-1}));
  const overrides=Object.entries(state.pageNumberPageOverrides).map(([key,t])=>{const [page,slot]=key.split(':');return {page:+page,slot,bbox:t.bbox,pageWidth:t.pageWidth,pageHeight:t.pageHeight,engine:t.engine,format:currentPageNumberFormat(slot)||t.format,sourceText:t.sourceText,sourceId:t.sourceId,captureMode:'box',sourceGroupCount:(t.numberGroups||[]).length};});
  try{const r=await fetch('/api/page-number-template/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,from:from-1,to:to-1,templates:payloadTemplates,overrides})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();state.pageNumberScanResults=j.results||[];state.pageNumberMatches=state.pageNumberScanResults;const anomalyCount=annotatePageNumberAnomalies();renderPageNumberResults();let replace=0,add=0,blockedBlank=0;for(const page of state.pageNumberScanResults)for(const sr of page.slots||[]){const t=templates.find(x=>x.slot===sr.slot);if(sr.found)replace++;else if(t?.allowBlankAdd)add++;else blockedBlank++;}els.pageNumberStatus.textContent=`扫描完成：识别 ${replace} 处；允许空白新增 ${add} 处；默认阻止空白新增 ${blockedBlank} 处${anomalyCount?`；${anomalyCount} 处未取得可靠数字坐标，需人工处理`:'。'}。`;els.pageNumberApply.disabled=!state.pageNumberScanResults.length;if(els.pageNumberAnomaly)els.pageNumberAnomaly.disabled=anomalyCount===0;}catch(e){els.pageNumberStatus.textContent=`扫描失败：${e.message}`;toast(e.message,5200);}finally{state.pageNumberBusy=false;els.pageNumberScan.disabled=false;}
}
function pageNumberReusableGlyph(oldText,newText){const d=singleCharDiff(oldText,newText);if(!d)return undefined;const clip=state.glyphLibrary.get(d.newChar);if(!clip||clip.documentId!==state.id)return undefined;return {...clip.asset,mode:clip.mode||'original',char:clip.char};}
function pageNumberTextEdit(item,page,newText,slot,template,role='field'){
  const engine=item.engine||template.engine||'electronic',reusable=engine==='scan'?pageNumberReusableGlyph(item.text,newText):undefined;return {type:'text',engine,page,id:`page-number-${slot}-${role}-${item.id}`,pageNumberSlot:slot,pageNumberRole:role,bbox:item.bbox,tokenBbox:item.tokenBbox||item.bbox,manualSelection:!!item.manualSelection,characterGeometry:!!item.characterGeometry,requiresIsolation:true,origin:item.origin||[item.bbox[0],item.bbox[3]],oldText:String(item.text||''),newText:String(newText),font:item.font||template.font,size:Number(item.size)||template.size,color:item.color||template.color,x:Number(item.origin?.[0]??item.bbox[0]),y:Number(item.origin?.[1]??item.bbox[3]),rotation:item.rotation||template.rotation||0,alpha:item.alpha??template.alpha??255,chars:item.chars||[],sameStyle:true,fontEmbedded:!!item.fontEmbedded,...(engine==='scan'?{visualAdjust:normalizeScanVisualAdjust(template.visualAdjust),...(reusable?{reusableGlyph:reusable}:{})}:{})};
}
function pageNumberVisualUnits(text){let units=0;for(const c of String(text||'')){if(/\s/.test(c))units+=.32;else if(/[0-9]/.test(c))units+=.62;else if(/[\/／|.-]/.test(c))units+=.45;else if(c.charCodeAt(0)>127)units+=1;else units+=.62;}return Math.max(.7,units);}
function pageNumberAnchor(template){const b=template?.bbox||[0,0,0,0],w=Math.max(1,Number(template?.pageWidth)||1),cx=(Number(b[0])+Number(b[2]))/2;if(cx<w*.38)return 'left';if(cx>w*.62)return 'right';return 'center';}
function pageNumberOutputBbox(base,target,template,sourceText=null,anchorOverride=null){const b=(base||template?.bbox||[0,0,1,1]).map(Number),h=Math.max(1,b[3]-b[1]),oldW=Math.max(2,b[2]-b[0]),source=String(sourceText??template?.sourceText??'0'),ratio=Math.max(1,pageNumberVisualUnits(target)/pageNumberVisualUnits(source)),pageW=Math.max(Number(template?.pageWidth)||b[2]+oldW,oldW),wanted=Math.min(pageW*.42,Math.max(oldW,oldW*ratio*1.08,h*pageNumberVisualUnits(target)*.45)),anchor=anchorOverride||pageNumberAnchor(template);let x0=b[0],x1=b[2];if(anchor==='left')x1=x0+wanted;else if(anchor==='right')x0=x1-wanted;else{x0=(b[0]+b[2]-wanted)/2;x1=x0+wanted;}if(x0<0){x1-=x0;x0=0;}if(x1>pageW){x0-=x1-pageW;x1=pageW;}return [Math.max(0,x0),b[1],Math.max(x0+2,x1),b[3]];}
function pageNumberDigitOutputBbox(base,oldText,newText,template){return pageNumberOutputBbox(base,newText,template,oldText,'center');}
function pageNumberAddEdit(sr,page,target,slot,template){const engine=sr.pageKind==='scan'?'scan':(template.engine||'electronic'),bbox=pageNumberOutputBbox(sr.expectedBbox,target,template,template.sourceText,pageNumberAnchor(template));return {type:'page-number-add',engine,page,id:`page-number-add-${slot}`,pageNumberSlot:slot,bbox,text:String(target),newText:String(target),font:template.font,size:template.size,color:template.color,alpha:template.alpha,rotation:template.rotation||0,originOffsetX:template.originOffsetX||0,originOffsetY:template.originOffsetY||Math.max(1,(template.bbox?.[3]-template.bbox?.[1])*.82),anchor:pageNumberAnchor(template),visualAdjust:normalizeScanVisualAdjust(template.visualAdjust)};}
function pageNumberReplaceEdit(sr,page,target,slot,template){const item=sr.item||{},base=item.bbox||sr.expectedBbox,engine=item.engine||template.engine||'electronic',outputBbox=pageNumberOutputBbox(base,target,template,item.text||sr.oldText,pageNumberAnchor({...template,bbox:base})),originY=Number(item.origin?.[1]??base?.[3]??0)-Number(base?.[1]??0);return {type:'page-number-replace',engine,page,id:`page-number-replace-${slot}-${item.id||page}`,pageNumberSlot:slot,bbox:base,outputBbox,oldText:String(sr.oldText||item.text||''),newText:String(target),text:String(target),font:item.font||template.font,size:Number(item.size)||template.size,color:item.color||template.color,alpha:item.alpha??template.alpha??255,rotation:item.rotation||template.rotation||0,originOffsetY:Number.isFinite(originY)&&originY>0?originY:(template.originOffsetY||Math.max(1,(base?.[3]-base?.[1])*.82)),anchor:pageNumberAnchor({...template,bbox:base}),visualAdjust:normalizeScanVisualAdjust(template.visualAdjust)};}
function pageNumberPartReplaceEdit(part,page,newValue,slot,template,role){const item=part.item||{},base=(item.bbox||[]).map(Number),engine=item.engine||template.engine||'electronic',outputBbox=pageNumberDigitOutputBbox(base,String(part.oldText||item.text||''),String(newValue),template),originY=Number(item.origin?.[1]??base?.[3]??0)-Number(base?.[1]??0);return {type:'page-number-replace',engine,page,id:`page-number-part-${slot}-${role}-${item.id||page}`,pageNumberSlot:slot,pageNumberRole:role,bbox:base,outputBbox,oldText:String(part.oldText||item.text||''),newText:String(newValue),text:String(newValue),font:item.font||template.font,size:Number(item.size)||template.size,color:item.color||template.color,alpha:item.alpha??template.alpha??255,rotation:item.rotation||template.rotation||0,originOffsetY:Number.isFinite(originY)&&originY>0?originY:Math.max(1,(base[3]-base[1])*.82),anchor:'center',tightNumeric:true,visualAdjust:normalizeScanVisualAdjust(template.visualAdjust)};}
function rolePageNumberValue(role,vals){return role==='total'?vals.total:role==='pdfpage'?vals.pdfpage:vals.current;}
function buildPageNumberPageEdits(result,templates){const vals=pageNumberValuesForPage(result.page),edits=[],unchanged=[],issues=[];for(const sr of result.slots||[]){const t=templates.get(sr.slot);if(!t)continue;const target=formatPageNumber(t.format,vals);if(sr.validation){issues.push({slot:sr.slot,text:sr.validation.text});continue;}if(!sr.found){if(t.allowBlankAdd)edits.push(pageNumberAddEdit(sr,result.page,target,sr.slot,t));else issues.push({slot:sr.slot,text:'未识别到原页码，且当前模板未开启“允许新增”。'});continue;}const roles=pageNumberRoles(t.format),parts=sr.parts||[];if(String(sr.oldText)===target&&parts.length<roles.length){unchanged.push({slot:sr.slot,role:'field'});continue;}
    // v2.3.24 restores the proven v2.3.21 rendering rule: formatted page
    // numbers are modified only through their existing numeric subfields. Fixed
    // literals such as 第 / 页 / 共 / , / / are never repainted as a whole phrase.
    if(parts.length>=roles.length&&roles.length>0){for(let i=0;i<roles.length;i++){const part=parts[i],role=part.role||roles[i],newValue=String(rolePageNumberValue(role,vals)),oldValue=String(part.oldText||'');if(oldValue===newValue){unchanged.push({slot:sr.slot,role});continue;}if(oldValue.length===newValue.length&&String(part.item?.engine||t.engine)==='scan')edits.push(pageNumberTextEdit(part.item,result.page,newValue,sr.slot,t,role));else edits.push(pageNumberPartReplaceEdit(part,result.page,newValue,sr.slot,t,role));}continue;}
    const literal=pageNumberLiteralText(t.format),old=String(sr.oldText||'');if(literal||/\D/.test(old)){issues.push({slot:sr.slot,text:'已识别到原页码，但未能可靠取得数字子区域；为避免叠字，不会整段重绘。请只对此页重新框选或手动接管。'});continue;}
    edits.push(pageNumberReplaceEdit(sr,result.page,target,sr.slot,t));}
  return {edits,unchanged,issues,vals};}
async function requestPreviewBlobForPage(page,pageEdits){const r=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page,scale:desiredRenderScale(),edits:pageEdits})});if(!r.ok)throw new Error(await apiError(r));return await r.blob();}
function setPageNumberRunStatus(page,slot,text,kind='ok'){const row=state.pageNumberScanResults.find(r=>r.page===page),sr=row?.slots?.find(x=>x.slot===slot);if(sr)sr.runStatus={text,kind};}
async function applyPageNumbers(){
  if(state.pageNumberBusy||!state.pageNumberScanResults.length)return;const templates=new Map(activePageNumberTemplates().map(t=>[t.slot,t]));if(!templates.size)return;annotatePageNumberAnomalies();const {from,to}=pageNumberRange(),start=+els.pageNumberStart.value||1,beforeBatch=snapshot(),batchId=`pn-${Date.now()}-${++state.pageNumberBatchSeq}`,historyLabel=`批量页码编辑：PDF 第 ${from}-${to} 页 · 从 ${start} 开始`,priorEntries=new Map();state.pageNumberBusy=true;els.pageNumberScan.disabled=true;els.pageNumberApply.disabled=true;beginPageProgress('正在逐页生成页码…');let historyStarted=false,replaceCount=0,addCount=0,failCount=0,unchangedCount=0;
  try{for(let i=0;i<state.pageNumberScanResults.length;i++){const r=state.pageNumberScanResults[i],percent=5+Math.round((i/state.pageNumberScanResults.length)*88);els.pageNumberStatus.textContent=`正在处理 PDF 第 ${r.page+1} 页（${i+1}/${state.pageNumberScanResults.length}）…`;setPageLoading(`正在渲染 PDF 第 ${r.page+1} 页…`,percent);const built=buildPageNumberPageEdits(r,templates);for(const u of built.unchanged){setPageNumberRunStatus(r.page,u.slot,'无需修改','skip');unchangedCount++;}for(const issue of built.issues||[]){setPageNumberRunStatus(r.page,issue.slot,issue.text,'fail');failCount++;}const accepted=[];const acceptedFeas=[];const groups=new Map();for(const e0 of built.edits){const e={...e0,pageNumberBatchId:batchId};if(!groups.has(e.pageNumberSlot))groups.set(e.pageNumberSlot,[]);groups.get(e.pageNumberSlot).push(e);}for(const [slot,slotEdits] of groups){const lockedExisting=allEdits().some(x=>x.page===r.page&&x.pageNumberSlot===slot&&x.locked);if(lockedExisting){setPageNumberRunStatus(r.page,slot,'对象已锁定，已跳过','fail');failCount++;continue;}const checked=[];let slotError='';for(const e of slotEdits){try{const f=await requestFeasibility(e);if(!editModeAllowed(f)){slotError=f?.reason||'未通过检查';break;}checked.push([e,f]);}catch(err){slotError=err.message;break;}}if(slotError){setPageNumberRunStatus(r.page,slot,slotError,'fail');failCount++;continue;}for(const pair of checked){accepted.push(pair[0]);acceptedFeas.push(pair);}}
      if(!accepted.length){renderPageNumberResults();continue;}const touchedSlots=new Set(accepted.map(e=>e.pageNumberSlot));const prior=allEdits().filter(e=>e.page===r.page&&!touchedSlots.has(e.pageNumberSlot));const candidate=[...prior,...accepted];try{await requestPreviewBlobForPage(r.page,candidate);}catch(err){for(const slot of new Set(accepted.map(e=>e.pageNumberSlot))){setPageNumberRunStatus(r.page,slot,`渲染失败：${err.message}`,'fail');failCount++;}renderPageNumberResults();continue;}
      if(!historyStarted){state.undo.push(beforeBatch);if(state.undo.length>80)state.undo.shift();state.redo=[];updateHistoryButtons();historyStarted=true;}
      for(const slot of touchedSlots){for(const [key,e] of [...state.edits.entries()])if(e.page===r.page&&e.pageNumberSlot===slot){if(!priorEntries.has(key))priorEntries.set(key,JSON.parse(JSON.stringify(e)));state.edits.delete(key);state.feasibility.delete(key);}}
      for(const [e,f] of acceptedFeas){const key=editKey(e.type,e.page,e.id);state.edits.set(key,e);state.feasibility.set(key,{...f,newText:e.newText||e.text,visualAdjust:e.visualAdjust,reusableGlyph:e.reusableGlyph});}
      for(const slot of touchedSlots){const slotEdits=accepted.filter(e=>e.pageNumberSlot===slot);if(slotEdits.some(e=>e.type==='page-number-add')){addCount++;setPageNumberRunStatus(r.page,slot,'已新增','ok');}else{replaceCount++;setPageNumberRunStatus(r.page,slot,'已按原位置修改','ok');}}
      updateChangeCount();renderPageNumberResults();}
    renderOverlays();await refreshPreview();if(historyStarted){captureVersion(historyLabel,{page:from,detail:`位置 ${[...templates.keys()].join(' / ')}`},true);state.lastPageNumberBatch={id:batchId,label:historyLabel,priorEntries:[...priorEntries.entries()],createdAt:Date.now()};}els.pageNumberStatus.textContent=`逐页生成完成：原位修改 ${replaceCount} 处，新增 ${addCount} 处，无需修改 ${unchangedCount} 处${failCount?`，需检查 ${failCount} 处`:''}。`;if(els.pageNumberAnomaly)els.pageNumberAnomaly.disabled=failCount===0&&!state.pageNumberScanResults.some(r=>(r.slots||[]).some(pageNumberResultIsBad));if(els.pageNumberUndoBatch)els.pageNumberUndoBatch.disabled=!state.lastPageNumberBatch;toast(`页码处理完成：原位修改 ${replaceCount} · 新增 ${addCount}${failCount?` · 需检查 ${failCount}`:''}`,5200);
  }catch(e){els.pageNumberStatus.textContent=`批量页码处理失败：${e.message}`;toast(e.message,6200);}finally{endPageProgress();state.pageNumberBusy=false;els.pageNumberScan.disabled=false;els.pageNumberApply.disabled=false;renderPageNumberResults();}
}
function deletePageNumberGroup(page,slot){const hits=[...state.edits.entries()].filter(([,e])=>e.page===page&&e.pageNumberSlot===slot);if(!hits.length)return toast('这一页该位置没有已生成的页码对象');if(hits.some(([,e])=>e.locked))return toast('该页码组包含已锁定对象，请先解锁');pushHistory(`删除页码组 ${slot}`,{page:page+1,detail:`${hits.length} 个对象`});for(const [key] of hits){state.edits.delete(key);state.feasibility.delete(key);}if(state.selected&&hits.some(([key])=>key===state.selected.key))clearProps();updateChangeCount();renderOverlays();renderPageNumberResults();schedulePreview(0);toast(`已删除 PDF 第 ${page+1} 页 · 位置 ${slot} 的页码组`);}
async function undoLastPageNumberBatch(){const batch=state.lastPageNumberBatch;if(!batch)return toast('没有可撤销的页码批量');const batchEntries=[...state.edits.entries()].filter(([,e])=>e.pageNumberBatchId===batch.id);pushHistory('撤销上次页码批量',{page:state.currentPage+1,detail:batch.label||batch.id});for(const [key] of batchEntries){state.edits.delete(key);state.feasibility.delete(key);}for(const [key,e] of batch.priorEntries||[]){state.edits.set(key,e);state.feasibility.delete(key);}state.lastPageNumberBatch=null;updateChangeCount();renderOverlays();renderPageNumberResults();if(els.pageNumberUndoBatch)els.pageNumberUndoBatch.disabled=true;await refreshPreview();toast(`已撤销上次页码批量，共移除 ${batchEntries.length} 个生成对象`,4200);}
if(els.pageNumberBtn)els.pageNumberBtn.onclick=openPageNumberModal;if(els.pageNumberClose)els.pageNumberClose.onclick=closePageNumberModal;if(els.pageNumberModal)els.pageNumberModal.onclick=e=>{if(e.target===els.pageNumberModal)closePageNumberModal();};if(els.pageNumberUseA)els.pageNumberUseA.onclick=()=>beginPageNumberBoxSelect('A');if(els.pageNumberUseB)els.pageNumberUseB.onclick=()=>beginPageNumberBoxSelect('B');if(els.pageNumberClearA)els.pageNumberClearA.onclick=()=>clearPageNumberTemplate('A');if(els.pageNumberClearB)els.pageNumberClearB.onclick=()=>clearPageNumberTemplate('B');if(els.pageNumberFormatA)els.pageNumberFormatA.onchange=()=>applyPageNumberPreset('A');if(els.pageNumberFormatB)els.pageNumberFormatB.onchange=()=>applyPageNumberPreset('B');if(els.pageNumberCustomA)els.pageNumberCustomA.onchange=()=>updatePageNumberCustom('A');if(els.pageNumberCustomB)els.pageNumberCustomB.onchange=()=>updatePageNumberCustom('B');[els.pageNumberFrom,els.pageNumberTo,els.pageNumberStart,els.pageNumberTotalMode,els.pageNumberTotalValue].filter(Boolean).forEach(x=>x.addEventListener('change',()=>invalidatePageNumberScan()));if(els.pageNumberScan)els.pageNumberScan.onclick=scanPageNumbers;if(els.pageNumberApply)els.pageNumberApply.onclick=applyPageNumbers;

window.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.pageNumberBoxSlot){cancelPageNumberBoxSelect({reopen:true});toast('已取消页码框选');return;}if(e.key==='Escape'&&els.pageNumberModal&&!els.pageNumberModal.classList.contains('hidden')){closePageNumberModal();return;}if(e.key==='Escape'&&els.historyModal&&!els.historyModal.classList.contains('hidden')){closeVersionHistory();return;}if(e.key==='Escape'&&state.manualSelectionRect){state.manualSelecting=false;clearManualRect();toast('已取消框选字段');return;}if((e.key==='Delete'||e.key==='Backspace')&&state.selected?.item?.manualSelection){clearProps();renderOverlays();toast('已取消手动字段选择');return;}if(e.key==='Escape'&&els.changeLogModal&&!els.changeLogModal.classList.contains('hidden')){closeChangeLog();return;}if(e.key==='Escape'&&els.deleteModal&&!els.deleteModal.classList.contains('hidden')){closeDeleteModal();return;}if(e.key==='Escape'&&!els.batchModal.classList.contains('hidden')){closeBatchModal();return;}if(e.key==='Escape'&&state.cleanPreview){state.cleanPreview=false;els.cleanPreview.classList.remove('active');els.cleanPreview.textContent='净图';renderOverlays();toast('已返回编辑模式');return;}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();els.undoBtn.click();}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'){e.preventDefault();els.redoBtn.click();}});


// ---------- v1.7 UI-only enhancements ----------
if(els.dropZone){['dragenter','dragover'].forEach(name=>els.dropZone.addEventListener(name,e=>{e.preventDefault();e.stopPropagation();els.dropZone.classList.add('dragover');}));['dragleave','drop'].forEach(name=>els.dropZone.addEventListener(name,e=>{e.preventDefault();e.stopPropagation();els.dropZone.classList.remove('dragover');}));els.dropZone.addEventListener('drop',e=>{const f=[...(e.dataTransfer?.files||[])].find(x=>x.name?.toLowerCase().endsWith('.pdf'));if(f)importPdf(f);else toast('请拖入 PDF 文件');});}

// ---------- v2.3.21 manual-control layer ----------
const V2321_RENDER_OVERLAYS = renderOverlays;
const V2321_SHOW_SELECTED_PROPS = showSelectedProps;
const V2321_BUILD_TEXT_EDIT = buildTextEdit;
const V2321_CLEAR_PROPS = clearProps;
const V2321_OPEN_PAGE_NUMBER_MODAL = openPageNumberModal;
const V2321_RENDER_PAGE_NUMBER_RESULTS = renderPageNumberResults;

function editIsMovable(e){return !!e&&['free-text','page-number-add','page-number-replace'].includes(String(e.type||''));}
function selectedStoredEdit(){return state.selected?state.edits.get(state.selected.key):null;}
function selectedIsLocked(){const e=selectedStoredEdit();return !!(e?.locked||state.selected?.item?.locked);}
function selectedBlockKind(){
  const e=selectedStoredEdit(),item=state.selected?.item;
  if(!state.selected||state.selected.type!=='text')return '';
  if(editIsMovable(e))return e.type;
  if(e?.type==='text'&&e.reusableGlyph)return 'reused-glyph';
  if(item?.freeText)return 'free-text';
  if(item?.manualSelection)return 'manual-region';
  return '';
}
function selectedBlockRect(){
  const e=selectedStoredEdit(),item=state.selected?.item,kind=selectedBlockKind();
  if(!kind)return null;
  if(e?.type==='page-number-replace')return [...(e.outputBbox||e.bbox||[])].map(Number);
  if(e?.type==='free-text'||e?.type==='page-number-add')return [...(e.bbox||[])].map(Number);
  if(kind==='reused-glyph'){
    const b=[...(e.bbox||item?.bbox||[])].map(Number);if(b.length!==4)return null;
    const a=normalizeScanVisualAdjust(e.visualAdjust),scale=4.0,dx=(+a.xOffsetPx||0)/scale,dy=(+a.yOffsetPx||0)/scale,sz=+a.sizeScale||1,ws=+a.widthScale||1,cx=(b[0]+b[2])/2+dx,cy=(b[1]+b[3])/2+dy,w=(b[2]-b[0])*sz*ws,h=(b[3]-b[1])*sz;
    return [cx-w/2,cy-h/2,cx+w/2,cy+h/2];
  }
  return [...(item?.bbox||[])].map(Number);
}
function originalSelectedRect(){
  const e=selectedStoredEdit(),item=state.selected?.item;
  if(e?.templateBbox?.length===4)return [...e.templateBbox].map(Number);
  if(item?.originalBbox?.length===4)return [...item.originalBbox].map(Number);
  if(e?.type==='page-number-replace'&&e.bbox?.length===4)return [...e.bbox].map(Number);
  return [...(item?.bbox||e?.bbox||[])].map(Number);
}
function updateGeometryInputs(){
  const r=selectedBlockRect(),lockable=!!selectedStoredEdit()||!!state.selected?.item?.manualSelection,show=(!!r&&r.length===4)||lockable;
  els.manualGeometrySection?.classList.toggle('hidden',!show);
  if(!show)return;
  const hasRect=!!r&&r.length===4;[els.blockX,els.blockY,els.blockW,els.blockH,els.resetBlockPosition,els.openDetailEditor].filter(Boolean).forEach(x=>x.disabled=!hasRect);
  if(hasRect){const [x0,y0,x1,y1]=r;els.blockX.value=(+x0).toFixed(1);els.blockY.value=(+y0).toFixed(1);els.blockW.value=Math.max(1,x1-x0).toFixed(1);els.blockH.value=Math.max(1,y1-y0).toFixed(1);}else{[els.blockX,els.blockY,els.blockW,els.blockH].filter(Boolean).forEach(x=>x.value='');}
  if(els.objectLockBtn){els.objectLockBtn.textContent=selectedIsLocked()?'解锁':'锁定';els.objectLockBtn.classList.toggle('active',selectedIsLocked());}
  if(els.reRecognizeBlock)els.reRecognizeBlock.disabled=!state.selected?.item?.manualSelection;
  if(els.convertFreeText)els.convertFreeText.disabled=!!state.selected?.item?.freeText||!!selectedStoredEdit()?.type&&selectedStoredEdit()?.type!=='text';
  if(els.resetBlockPosition)els.resetBlockPosition.disabled=!hasRect||!originalSelectedRect()?.length;
}
function clampRectToPage(r){const w=Number(state.pageData?.width)||99999,h=Number(state.pageData?.height)||99999;let [x0,y0,x1,y1]=r.map(Number),rw=Math.max(1,x1-x0),rh=Math.max(1,y1-y0);if(x0<0){x1-=x0;x0=0;}if(y0<0){y1-=y0;y0=0;}if(x1>w){x0-=x1-w;x1=w;}if(y1>h){y0-=y1-h;y1=h;}x0=Math.max(0,x0);y0=Math.max(0,y0);return [x0,y0,Math.max(x0+1,Math.min(w,x0+rw)),Math.max(y0+1,Math.min(h,y0+rh))];}
function commitSelectedRect(rect,{history=true,preview=true,label='移动 / 调整字块'}={}){
  if(!state.selected||selectedIsLocked())return false;rect=clampRectToPage(rect);const e=selectedStoredEdit(),kind=selectedBlockKind(),item=state.selected.item;if(!kind)return false;
  if(history&&e)pushHistory(label,{page:state.currentPage+1,detail:String(e.newText||e.text||'')});
  if(e?.type==='page-number-replace'){e.outputBbox=[...rect];e.locked=!!e.locked;state.edits.set(state.selected.key,e);state.feasibility.delete(state.selected.key);}
  else if(e?.type==='free-text'||e?.type==='page-number-add'){e.bbox=[...rect];e.templateBbox=e.templateBbox||originalSelectedRect();state.edits.set(state.selected.key,e);state.feasibility.delete(state.selected.key);if(item){item.bbox=[...rect];item.origin=[rect[0],rect[3]];}}
  else if(kind==='reused-glyph'&&e){const b=[...(e.bbox||item.bbox)].map(Number),baseCx=(b[0]+b[2])/2,baseCy=(b[1]+b[3])/2,newCx=(rect[0]+rect[2])/2,newCy=(rect[1]+rect[3])/2,baseW=Math.max(.1,b[2]-b[0]),baseH=Math.max(.1,b[3]-b[1]),newW=Math.max(.1,rect[2]-rect[0]),newH=Math.max(.1,rect[3]-rect[1]),size=Math.max(.5,Math.min(1.5,newH/baseH)),width=Math.max(.5,Math.min(1.5,(newW/baseW)/size));e.visualAdjust=normalizeScanVisualAdjust({...e.visualAdjust,sizeScale:size,widthScale:width,xOffsetPx:(newCx-baseCx)*4,yOffsetPx:(newCy-baseCy)*4});state.edits.set(state.selected.key,e);state.feasibility.delete(state.selected.key);loadScanVisualAdjust(e.visualAdjust);}
  else if(item?.manualSelection&&e?.type==='text'){e.bbox=[...rect];e.tokenBbox=[...rect];e.origin=[rect[0],rect[3]];e.manualSelection=true;state.edits.set(state.selected.key,e);state.feasibility.delete(state.selected.key);item.bbox=[...rect];item.tokenBbox=[...rect];item.origin=[rect[0],rect[3]];item.originalBbox=item.originalBbox||[...rect];}
  else if(item?.manualSelection){item.bbox=[...rect];item.tokenBbox=[...rect];item.origin=[rect[0],rect[3]];item.originalBbox=item.originalBbox||[...rect];}
  updateGeometryInputs();renderOverlays();renderObjectLayer();if(preview&&e){updateChangeCount();schedulePreview(0);}else if(item?.manualSelection){updatePrecisionMode();markRunPending();}return true;
}
function geometryInputRect(){const x=Number(els.blockX?.value),y=Number(els.blockY?.value),w=Math.max(1,Number(els.blockW?.value)||1),h=Math.max(1,Number(els.blockH?.value)||1);if(![x,y,w,h].every(Number.isFinite))return null;return [x,y,x+w,y+h];}
function snapMovingRect(rect){
  if(!state.snapEnabled)return {rect,guides:{}};const src=originalSelectedRect(),w=rect[2]-rect[0],h=rect[3]-rect[1],cx=(rect[0]+rect[2])/2,cy=(rect[1]+rect[3])/2,threshold=2.2;let dx=0,dy=0,gx=null,gy=null,bestX=threshold,bestY=threshold;
  const xTargets=[],yTargets=[];if(src?.length===4){xTargets.push((src[0]+src[2])/2,src[0],src[2]);yTargets.push((src[1]+src[3])/2,src[3],src[1]);}
  for(const t of state.pageData?.text||[]){if(t.id===state.selected?.item?.id)continue;const b=t.bbox||[];if(b.length!==4)continue;xTargets.push(+b[0],(+b[0]+ +b[2])/2,+b[2]);yTargets.push(+b[3],+b[1]);}
  for(const target of xTargets){for(const anchor of [rect[0],cx,rect[2]]){const d=target-anchor;if(Math.abs(d)<bestX){bestX=Math.abs(d);dx=d;gx=target;}}}
  for(const target of yTargets){for(const anchor of [rect[1],cy,rect[3]]){const d=target-anchor;if(Math.abs(d)<bestY){bestY=Math.abs(d);dy=d;gy=target;}}}
  return {rect:[rect[0]+dx,rect[1]+dy,rect[0]+dx+w,rect[1]+dy+h],guides:{x:gx,y:gy}};
}
function drawSnapGuides(guides={}){els.overlayLayer.querySelectorAll('.snap-guide').forEach(x=>x.remove());if(guides.x!=null){const g=document.createElement('i');g.className='snap-guide v';g.style.left=`${toPx(guides.x)}px`;els.overlayLayer.appendChild(g);}if(guides.y!=null){const g=document.createElement('i');g.className='snap-guide h';g.style.top=`${toPx(guides.y)}px`;els.overlayLayer.appendChild(g);}}
function createTransformOverlay(){
  const rect=selectedBlockRect();if(!rect||rect.length!==4||state.cleanPreview)return;const box=document.createElement('div');box.className='transform-box'+(selectedIsLocked()?' locked':'');box.dataset.testid='transform-box';const [x0,y0,x1,y1]=rect;Object.assign(box.style,{left:`${toPx(x0)}px`,top:`${toPx(y0)}px`,width:`${Math.max(4,toPx(x1-x0))}px`,height:`${Math.max(4,toPx(y1-y0))}px`});
  for(const h of ['nw','n','ne','e','se','s','sw','w']){const dot=document.createElement('i');dot.className='transform-handle';dot.dataset.handle=h;box.appendChild(dot);}
  box.onpointerdown=e=>{if(selectedIsLocked())return;e.preventDefault();e.stopPropagation();const handle=e.target.closest('.transform-handle')?.dataset.handle||'move';state.transformDrag={handle,startX:e.clientX,startY:e.clientY,startRect:[...rect],box};box.setPointerCapture?.(e.pointerId);};els.overlayLayer.appendChild(box);
}
function transformRectFromPointer(d,e){const k=state.scale*state.zoom,dx=(e.clientX-d.startX)/k,dy=(e.clientY-d.startY)/k,r=[...d.startRect],h=d.handle;let out;if(h==='move')out=[r[0]+dx,r[1]+dy,r[2]+dx,r[3]+dy];else{out=[...r];if(h.includes('w'))out[0]=Math.min(r[2]-1,r[0]+dx);if(h.includes('e'))out[2]=Math.max(r[0]+1,r[2]+dx);if(h.includes('n'))out[1]=Math.min(r[3]-1,r[1]+dy);if(h.includes('s'))out[3]=Math.max(r[1]+1,r[3]+dy);}if(h==='move')return snapMovingRect(out);return {rect:clampRectToPage(out),guides:{}};}
window.addEventListener('pointermove',e=>{const d=state.transformDrag;if(!d)return;const x=transformRectFromPointer(d,e),r=x.rect;Object.assign(d.box.style,{left:`${toPx(r[0])}px`,top:`${toPx(r[1])}px`,width:`${Math.max(4,toPx(r[2]-r[0]))}px`,height:`${Math.max(4,toPx(r[3]-r[1]))}px`});drawSnapGuides(x.guides);d.currentRect=r;});
window.addEventListener('pointerup',()=>{const d=state.transformDrag;if(!d)return;state.transformDrag=null;els.overlayLayer.querySelectorAll('.snap-guide').forEach(x=>x.remove());commitSelectedRect(d.currentRect||d.startRect,{history:true,preview:true,label:d.handle==='move'?'移动字块':'调整字块大小'});});

function editOverlayItem(e,key){const b=(e.type==='page-number-replace'?(e.outputBbox||e.bbox):e.bbox)||[];return {id:e.id,engine:e.engine||'electronic',text:String(e.newText||e.text||e.oldText||''),bbox:[...b],tokenBbox:e.bbox||b,origin:e.origin||[b[0]||0,b[3]||0],size:e.size||Math.max(6,(b[3]||0)-(b[1]||0)),color:e.color||'#000000',font:e.font||'',manualSelection:!!e.manualSelection,freeText:e.type==='free-text',_editKey:key,_editType:e.type,locked:!!e.locked,originalBbox:e.templateBbox||e.bbox};}
function addEditOverlays(){for(const [key,e] of state.edits.entries()){if(e.page!==state.currentPage||!['free-text','page-number-add','page-number-replace'].includes(e.type))continue;const b=e.type==='page-number-replace'?(e.outputBbox||e.bbox):e.bbox;if(!b?.length)continue;const box=document.createElement('div');box.className='obj-box text-box edited generated-edit'+(key===state.selected?.key?' selected':'');Object.assign(box.style,{left:`${toPx(b[0])}px`,top:`${toPx(b[1])}px`,width:`${Math.max(3,toPx(b[2]-b[0]))}px`,height:`${Math.max(4,toPx(b[3]-b[1]))}px`});box.title=`${e.type==='free-text'?'新增文字':'页码'}：${e.newText||e.text||''} · 单击可选中`;box.dataset.editKey=key;box.onpointerdown=ev=>{if(state.cleanPreview)return;ev.preventDefault();ev.stopPropagation();selectEditFromLayer(key,e);};els.overlayLayer.appendChild(box);}}
renderOverlays=function(){V2321_RENDER_OVERLAYS();if(!state.pageData||state.cleanPreview)return;addEditOverlays();createTransformOverlay();renderObjectLayer();};

clearProps=function(){V2321_CLEAR_PROPS();els.manualGeometrySection?.classList.add('hidden');renderObjectLayer();};
showSelectedProps=function(){
  if(!state.selected)return clearProps();const e=selectedStoredEdit(),item=state.selected.item;
  V2321_SHOW_SELECTED_PROPS();
  if(e&&['free-text','page-number-add','page-number-replace'].includes(e.type)){
    els.objectType.textContent=e.type==='free-text'?'可移动字块':'页码字块';els.textContent.value=String(e.newText||e.text||'');els.fontSize.value=e.size||item.size||10;els.fontColor.value=e.color||'#000000';els.fontName.value=e.font||'自由文字';[els.fontSize,els.fontColor].forEach(x=>x.disabled=false);[els.textX,els.textY].forEach(x=>x.disabled=true);els.scanTuneSection?.classList.toggle('hidden',String(e.engine)!=='scan');if(e.engine==='scan')loadScanVisualAdjust(e.visualAdjust);renderFeasibilityStatus(state.feasibility.get(state.selected.key)||{mode:e.type==='free-text'?'free-text':e.type,visualVerified:true,reason:'可移动字块'});markRunPending();
  }else if(item?.freeText){els.objectType.textContent='新增文字';[els.fontSize,els.fontColor].forEach(x=>x.disabled=false);[els.textX,els.textY].forEach(x=>x.disabled=true);els.scanTuneSection?.classList.toggle('hidden',item.engine!=='scan');if(item.engine==='scan')updateFinalGlyphPreview();}
  updateGeometryInputs();renderObjectLayer();
};

buildTextEdit=function(item){
  const stored=state.selected?state.edits.get(state.selected.key):null;
  if(stored&&['free-text','page-number-add','page-number-replace'].includes(stored.type)){
    const edit={...stored,newText:els.textContent.value,text:els.textContent.value,size:+els.fontSize.value||stored.size,color:els.fontColor.value||stored.color};if(edit.engine==='scan')edit.visualAdjust=readScanVisualAdjust();return edit;
  }
  if(item?.freeText){const bbox=[...(item.bbox||[])],engine=item.engine||((state.pageData?.pageKind==='scan')?'scan':'electronic'),visualAdjust=engine==='scan'?readScanVisualAdjust():undefined;return {type:'free-text',engine,page:state.currentPage,id:item.id,bbox,text:els.textContent.value,newText:els.textContent.value,oldText:'',font:item.font||'Times New Roman',size:+els.fontSize.value||item.size||Math.max(7,bbox[3]-bbox[1]),color:els.fontColor.value||item.color||'#000000',alpha:item.alpha??255,rotation:0,sameStyle:true,x:bbox[0],y:bbox[3],templateBbox:item.originalBbox||bbox,locked:!!item.locked,dataUrl:item.dataUrl||'',...(engine==='scan'?{visualAdjust}:{})};}
  return V2321_BUILD_TEXT_EDIT(item);
};

function createFreeTextSelection(rect,text='',template={}){const id=`free-${Date.now()}-${Math.random().toString(36).slice(2,6)}`,engine=template.engine||((state.pageData?.pageKind==='scan')?'scan':'electronic'),item={id,engine,text:String(text||''),bbox:[...rect],tokenBbox:[...rect],origin:[rect[0],rect[3]],size:template.size||Math.max(7,(rect[3]-rect[1])*.75),color:template.color||'#000000',font:template.font||(engine==='scan'?'扫描新增文字':'Times New Roman'),manualSelection:true,freeText:true,sourceText:'自由新增文字',originalBbox:[...rect],dataUrl:template.dataUrl||'',visualAdjust:template.visualAdjust};selectObject('text',item,editKey('free-text',state.currentPage,id));if(template.visualAdjust&&engine==='scan')loadScanVisualAdjust(template.visualAdjust);return item;}
completeManualSelection=async function(){const raw=state.manualSelectionRect;if(!raw)return;const rect=clampRectToPage(raw);if(rect[2]-rect[0]<3||rect[3]-rect[1]<3){clearManualRect();return;}const addOnly=state.selectionMode==='manual-add';showLoading(true);try{if(addOnly){clearManualRect();createFreeTextSelection(rect,'');toast('已创建空白可移动文字块，请输入内容后运行');return;}const r=await fetch('/api/manual-region',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,bbox:rect,allowEmpty:true})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json(),f=j.field||{},hasText=!!String(f.text||'').trim();const item={id:`manual-${Date.now()}`,engine:(j.pageKind||state.pageData?.pageKind)==='scan'?'scan':'electronic',text:String(f.text||''),bbox:[...rect],tokenBbox:[...rect],origin:[rect[0],rect[3]],chars:f.chars||[],size:Math.max(7,rect[3]-rect[1]),color:'#000000',font:(j.pageKind||state.pageData?.pageKind)==='scan'?'扫描 OCR 修订':'手动框选文字',manualSelection:true,sourceText:hasText?'手动框选识别':'框内未识别到文字',originalBbox:[...rect],freeText:!hasText};clearManualRect();selectObject('text',item,editKey(hasText?'text':'free-text',state.currentPage,item.id));toast(hasText?`已按你的框选范围识别：“${item.text}”`:'框内未识别到原字，已转为自由新增文字块',4200);}catch(err){clearManualRect();toast(err.message,5200);}finally{showLoading(false);}};

async function reRecognizeSelectedBlock(){const item=state.selected?.item,rect=selectedBlockRect();if(!item?.manualSelection||!rect)return;showLoading(true);try{const r=await fetch('/api/manual-region',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,bbox:rect,allowEmpty:true})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json(),f=j.field||{};item.text=String(f.text||'');item.sourceText=item.text?'手动重新识别':'框内未识别到文字';item.chars=f.chars||[];item.freeText=!item.text;item.engine=(j.pageKind||state.pageData?.pageKind)==='scan'?'scan':'electronic';state.selected.key=editKey(item.freeText?'free-text':'text',state.currentPage,item.id);showSelectedProps();renderOverlays();toast(item.text?`重新识别：${item.text}`:'仍未识别到文字，已保留为空白新增字块');}catch(e){toast(e.message,5200);}finally{showLoading(false);}}
function convertSelectedToFreeText(){const item=state.selected?.item;if(!item||state.selected.type!=='text')return;const rect=selectedBlockRect()||item.bbox;const content=String(els.textContent.value||item.text||'');item.freeText=true;item.text=content;item.sourceText='人工新增文字';item.originalBbox=item.originalBbox||[...rect];item.bbox=[...rect];state.selected.key=editKey('free-text',state.currentPage,item.id);showSelectedProps();renderOverlays();toast('已转为自由新增字块，可直接拖动、缩放和重新输入内容');}
function toggleSelectedLock(){if(!state.selected)return;const e=selectedStoredEdit();if(e){pushHistory(e.locked?'解锁字块':'锁定字块',{page:state.currentPage+1,detail:e.newText||e.text||''});e.locked=!e.locked;state.edits.set(state.selected.key,e);updateChangeCount();}else state.selected.item.locked=!state.selected.item.locked;updateGeometryInputs();renderOverlays();renderObjectLayer();toast(selectedIsLocked()?'已锁定：不会误拖、缩放或被批量覆盖':'已解锁');}
function resetSelectedBlockPosition(){const r=originalSelectedRect();if(!r?.length)return;commitSelectedRect(r,{history:true,preview:true,label:'复位字块位置'});}

function captureSelectedBlockSprite(){const rect=selectedBlockRect();if(!rect?.length||!els.pageImage?.naturalWidth||!state.pageData)return '';const sx=els.pageImage.naturalWidth/Math.max(1,state.pageData.width),sy=els.pageImage.naturalHeight/Math.max(1,state.pageData.height),x=Math.max(0,Math.round(rect[0]*sx)),y=Math.max(0,Math.round(rect[1]*sy)),w=Math.max(1,Math.round((rect[2]-rect[0])*sx)),h=Math.max(1,Math.round((rect[3]-rect[1])*sy)),c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(els.pageImage,x,y,w,h,0,0,w,h);const im=ctx.getImageData(0,0,w,h),d=im.data,idxs=[[1,1],[Math.max(0,w-2),1],[1,Math.max(0,h-2)],[Math.max(0,w-2),Math.max(0,h-2)]],bg=[0,0,0];for(const [px,py] of idxs){const i=(py*w+px)*4;bg[0]+=d[i];bg[1]+=d[i+1];bg[2]+=d[i+2];}bg=bg.map(v=>v/idxs.length);for(let i=0;i<d.length;i+=4){const dist=Math.sqrt((d[i]-bg[0])**2+(d[i+1]-bg[1])**2+(d[i+2]-bg[2])**2),a=Math.max(0,Math.min(255,(dist-7)*16));d[i+3]=a;}ctx.putImageData(im,0,0);return c.toDataURL('image/png');}
function renderFinishedBlockLibrary(){if(!els.finishedBlockLibrary)return;els.finishedBlockLibrary.innerHTML='';if(!state.blockLibrary?.size){els.finishedBlockLibrary.innerHTML='<span class="finished-glyph-empty">当前文档字组为空</span>';return;}for(const [name,b] of state.blockLibrary.entries()){const el=document.createElement('button');el.type='button';el.className='finished-block-chip'+(state.blockClipboard?.id===b.id?' active':'');el.textContent=name;el.title=`选择成品字组：${name}`;el.onclick=()=>{state.blockClipboard=b;renderFinishedBlockLibrary();toast(`已选择成品字组“${name}”`);};els.finishedBlockLibrary.appendChild(el);}}
function saveSelectedFinishedBlock(){const edit=selectedStoredEdit();if(!state.selected||state.selected.type!=='text'||!edit)return toast('请先运行并确认一个文字修改，再保存成品字组');const rect=selectedBlockRect()||edit.bbox,text=String(edit.newText||edit.text||'').trim();if(!text)return toast('当前字块没有文字内容');const sprite=captureSelectedBlockSprite(),tpl={id:`block-${Date.now()}`,documentId:state.id,text,width:rect[2]-rect[0],height:rect[3]-rect[1],engine:edit.engine||'scan',font:edit.font||'',size:edit.size||10,color:edit.color||'#000000',visualAdjust:normalizeScanVisualAdjust(edit.visualAdjust),dataUrl:sprite};state.blockLibrary.set(text,tpl);state.blockClipboard=tpl;renderFinishedBlockLibrary();toast(`已保存成品字组“${text}”，可作为可移动字块复用`);}
async function pasteFinishedBlockAsFree(){const b=state.blockClipboard;if(!b)return toast('请先保存或选择一个成品字组 / 短语');if(b.documentId!==state.id)return toast('成品字组仅在当前 PDF 内复用');const anchor=selectedBlockRect(),pw=Number(state.pageData?.width)||595,ph=Number(state.pageData?.height)||842,w=Math.max(2,b.width||30),h=Math.max(2,b.height||12),x=anchor?anchor[0]:Math.max(0,(pw-w)/2),y=anchor?anchor[1]:Math.max(0,(ph-h)/2),item=createFreeTextSelection(clampRectToPage([x,y,x+w,y+h]),b.text,b);els.textContent.value=b.text;const ok=await runSelectedEdit();if(ok){toast('成品字组已粘贴为可移动字块：可直接拖动到任意位置');renderOverlays();}}

function selectEditFromLayer(key,e){const item=editOverlayItem(e,key);selectObject('text',item,key);}
function renderObjectLayer(){if(!els.objectLayerPanel||!els.objectLayerList)return;els.objectLayerPanel.classList.toggle('hidden',!state.objectLayerOpen);if(!state.objectLayerOpen)return;els.objectLayerList.innerHTML='';const rows=[];for(const [key,e] of state.edits.entries())if(e.page===state.currentPage){const role=e.pageNumberRole?`页码·${PAGE_NUMBER_ROLE_LABELS[e.pageNumberRole]||e.pageNumberRole}·${e.pageNumberSlot||''}`:(e.pageNumberSlot?`页码组·${e.pageNumberSlot}`:e.type);rows.push({kind:e.type==='image'?'🖼':'T',label:String(e.newText||e.text||e.oldText||e.name||e.type),meta:e.locked?`已锁定 · ${role}`:role,key,e,edited:true});}if(state.objectLayerAll){for(const t of state.pageData?.text||[]){const key=editKey('text',state.currentPage,t.id);if(state.edits.has(key))continue;rows.push({kind:'T',label:t.text,meta:'识别文字',key,item:t,type:'text'});}for(const im of state.pageData?.images||[]){const key=editKey('image',state.currentPage,im.id);if(state.edits.has(key))continue;rows.push({kind:'🖼',label:'图片',meta:'识别图片',key,item:im,type:'image'});}}if(state.selected?.item?.manualSelection&&!rows.some(r=>r.key===state.selected.key))rows.unshift({kind:'□',label:state.selected.item.text||'空白新增文字',meta:'当前手动框选',key:state.selected.key,item:state.selected.item,type:'text'});if(!rows.length){els.objectLayerList.innerHTML='<div class="history-empty">当前页还没有手动或已编辑对象。</div>';return;}for(const r of rows){const b=document.createElement('button');b.type='button';b.className='object-layer-item'+(r.key===state.selected?.key?' active':'');b.innerHTML=`<span class="kind">${r.kind}</span><span class="label">${escapeHtml(r.label||'—')}</span><span class="meta">${escapeHtml(r.meta||'')}</span>`;b.onclick=()=>{if(r.e)selectEditFromLayer(r.key,r.e);else if(r.item)selectObject(r.type||'text',r.item,r.key);};els.objectLayerList.appendChild(b);}}
function toggleObjectLayer(force){state.objectLayerOpen=typeof force==='boolean'?force:!state.objectLayerOpen;renderObjectLayer();els.objectLayerToggle?.classList.toggle('active',state.objectLayerOpen);}

function renderDetailEditor(){const rect=selectedBlockRect();if(!rect?.length||!els.detailCanvas||!els.pageImage?.naturalWidth)return;const pad=Math.max(6,Math.min(20,(rect[3]-rect[1])*1.8)),pw=Number(state.pageData?.width)||1,ph=Number(state.pageData?.height)||1,crop=[Math.max(0,rect[0]-pad),Math.max(0,rect[1]-pad),Math.min(pw,rect[2]+pad),Math.min(ph,rect[3]+pad)],z=state.detailZoom||4,c=els.detailCanvas;c.width=Math.max(100,Math.round((crop[2]-crop[0])*z));c.height=Math.max(100,Math.round((crop[3]-crop[1])*z));const ctx=c.getContext('2d'),sx=els.pageImage.naturalWidth/pw,sy=els.pageImage.naturalHeight/ph;ctx.drawImage(els.pageImage,crop[0]*sx,crop[1]*sy,(crop[2]-crop[0])*sx,(crop[3]-crop[1])*sy,0,0,c.width,c.height);state.detailCrop=crop;const o=els.detailObject;o.classList.remove('hidden');Object.assign(o.style,{left:`${(rect[0]-crop[0])*z}px`,top:`${(rect[1]-crop[1])*z}px`,width:`${Math.max(5,(rect[2]-rect[0])*z)}px`,height:`${Math.max(5,(rect[3]-rect[1])*z)}px`});els.detailEditorInfo.textContent=`${Math.round(z*100)}% · X ${rect[0].toFixed(1)} / Y ${rect[1].toFixed(1)}`;}
function openDetailEditor(){if(!selectedBlockRect())return toast('当前对象不支持局部拖动编辑');els.detailEditorModal.classList.remove('hidden');renderDetailEditor();}
function closeDetailEditor(){els.detailEditorModal?.classList.add('hidden');}
let detailDrag=null;if(els.detailObject)els.detailObject.onpointerdown=e=>{if(selectedIsLocked())return;e.preventDefault();e.stopPropagation();const r=selectedBlockRect();detailDrag={x:e.clientX,y:e.clientY,rect:r};els.detailObject.setPointerCapture?.(e.pointerId);};
window.addEventListener('pointermove',e=>{if(!detailDrag)return;const z=state.detailZoom||4,dx=(e.clientX-detailDrag.x)/z,dy=(e.clientY-detailDrag.y)/z,r=detailDrag.rect,out=snapMovingRect([r[0]+dx,r[1]+dy,r[2]+dx,r[3]+dy]).rect,crop=state.detailCrop;Object.assign(els.detailObject.style,{left:`${(out[0]-crop[0])*z}px`,top:`${(out[1]-crop[1])*z}px`});detailDrag.current=out;});window.addEventListener('pointerup',()=>{if(!detailDrag)return;const r=detailDrag.current||detailDrag.rect;detailDrag=null;commitSelectedRect(r,{history:true,preview:true,label:'局部放大移动字块'});setTimeout(renderDetailEditor,120);});

async function trialBatchEdits(){if(state.batchBusy||!state.batchSource)return;const selected=batchCheckboxes().filter(x=>x.checked).map(x=>+x.dataset.page);if(!selected.length)return toast('请先选择要批量处理的页面');const pages=[selected[0],selected[Math.floor((selected.length-1)/2)],selected[selected.length-1]].filter((v,i,a)=>a.indexOf(v)===i),matches=pages.map(p=>state.batchMatches.find(m=>m.page===p)).filter(Boolean);state.batchBusy=true;els.batchTrial.disabled=true;els.batchResult.classList.remove('hidden','trial-ok','trial-fail');els.batchScanStatus.textContent=`正在试运行 ${matches.length} 个代表页…`;let ok=0,fail=[];try{for(const m of matches){const key=editKey('text',m.page,m.item?.id||''),locked=state.edits.get(key)?.locked;if(locked){fail.push(`第 ${m.page+1} 页：对象已锁定`);continue;}const e=targetEditFromMatch(m,state.batchSource.newText);try{const f=await requestFeasibility(e);if(!editModeAllowed(f))throw new Error(f.reason||'未通过检查');const prior=allEdits().filter(x=>x.page===m.page&&!(x.type==='text'&&x.id===e.id));await requestPreviewBlobForPage(m.page,[...prior,e]);ok++;}catch(err){fail.push(`第 ${m.page+1} 页：${err.message}`);}}els.batchResult.classList.add(fail.length?'trial-fail':'trial-ok');els.batchResult.innerHTML=`<strong>3 页试运行：通过 ${ok} 页${fail.length?`，失败 ${fail.length} 页`:'，可以继续全量'}</strong>${fail.length?'<br>'+fail.map(escapeHtml).join('<br>'):''}`;els.batchScanStatus.textContent='试运行完成（未写入修改）';}finally{state.batchBusy=false;els.batchTrial.disabled=false;}}
async function trialPageNumbers(){if(state.pageNumberBusy||!state.pageNumberScanResults.length)return;const rows=state.pageNumberScanResults,tries=[rows[0],rows[Math.floor((rows.length-1)/2)],rows[rows.length-1]].filter((v,i,a)=>v&&a.indexOf(v)===i),templates=new Map(activePageNumberTemplates().map(t=>[t.slot,t]));state.pageNumberBusy=true;els.pageNumberTrial.disabled=true;let ok=0,fail=[];try{for(const r of tries){const built=buildPageNumberPageEdits(r,templates),accepted=[];try{if(built.issues?.length)throw new Error(built.issues.map(x=>x.text).join('；'));for(const e of built.edits){const locked=allEdits().some(x=>x.page===r.page&&x.pageNumberSlot===e.pageNumberSlot&&x.locked);if(locked)throw new Error(`位置 ${e.pageNumberSlot} 已锁定`);const f=await requestFeasibility(e);if(!editModeAllowed(f))throw new Error(f.reason||'未通过检查');accepted.push(e);}const touched=new Set(accepted.map(x=>x.pageNumberSlot)),prior=allEdits().filter(x=>x.page===r.page&&!touched.has(x.pageNumberSlot));await requestPreviewBlobForPage(r.page,[...prior,...accepted]);ok++;}catch(err){fail.push(`第 ${r.page+1} 页：${err.message}`);}}els.pageNumberStatus.textContent=`3 页试运行：通过 ${ok}/${tries.length}${fail.length?'；'+fail.join('；'):'，可以继续逐页生成'}（未写入修改）`;toast(fail.length?'页码试运行存在异常，请先检查':'页码 3 页试运行通过，可以继续全量',4200);}finally{state.pageNumberBusy=false;els.pageNumberTrial.disabled=false;}}

// Dynamic page-number slots: A/B remain by default; C/D/... may be added freely.
pageNumberSlotEls=function(slot){if(slot==='A')return {use:els.pageNumberUseA,clear:els.pageNumberClearA,state:els.pageNumberSlotAState,format:els.pageNumberFormatA,custom:els.pageNumberCustomA,rangeFrom:els.pageNumberRangeFromA,rangeTo:els.pageNumberRangeToA,allowAdd:els.pageNumberAllowAddA};if(slot==='B')return {use:els.pageNumberUseB,clear:els.pageNumberClearB,state:els.pageNumberSlotBState,format:els.pageNumberFormatB,custom:els.pageNumberCustomB,rangeFrom:els.pageNumberRangeFromB,rangeTo:els.pageNumberRangeToB,allowAdd:els.pageNumberAllowAddB};const card=els.pageNumberSlotGrid?.querySelector(`[data-slot="${slot}"]`);return {use:card?.querySelector('.slot-use'),clear:card?.querySelector('.slot-clear'),state:card?.querySelector('.slot-state'),format:card?.querySelector('.slot-format'),custom:card?.querySelector('.slot-custom'),rangeFrom:card?.querySelector('.slot-range-from'),rangeTo:card?.querySelector('.slot-range-to'),allowAdd:card?.querySelector('.slot-allow-add')};};
function pageNumberSlots(){return Object.keys(state.pageNumberTemplates).sort();}
function addPageNumberSlot(){const existing=pageNumberSlots(),alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ',slot=[...alphabet].find(x=>!existing.includes(x))||`P${existing.length+1}`;state.pageNumberTemplates[slot]=null;const card=document.createElement('section');card.className='page-number-slot-card dynamic-slot';card.dataset.slot=slot;const global=pageNumberRange();card.innerHTML=`<div class="page-number-slot-head"><div><span class="slot-badge">${slot}</span><strong>页码位置 ${slot}</strong></div><div class="slot-actions"><button class="mini-btn soft-btn slot-use" type="button">框选位置 ${slot}</button><button class="mini-btn soft-btn slot-clear" type="button">清除</button><button class="mini-btn soft-btn remove-dynamic-slot" type="button">删除位置</button></div></div><div class="page-number-slot-state slot-state">未设置</div><label>这个框修改什么</label><select class="slot-role"><option value="auto">自动识别</option><option value="current">只改“第几页”</option><option value="total">只改“共几页”</option><option value="both">当前页 + 总页数</option></select><label class="hidden">显示格式</label><select class="slot-format hidden"><option value="current">当前页：{current}</option><option value="current_total_slash">当前 / 总页数：{current}/{total}</option><option value="current_total_cn">中文：第{current}页，共{total}页</option><option value="total">仅总页数：{total}</option><option value="custom">自定义</option></select><label class="hidden">模板</label><input class="page-number-template-input slot-custom hidden" type="text" value="{current}" /><div class="slot-range-row"><label>适用 PDF 页</label><div><input class="slot-range-from" type="number" min="1" value="${global.from}" /><span>—</span><input class="slot-range-to" type="number" min="1" value="${global.to}" /></div></div><label class="slot-check"><input class="slot-allow-add" type="checkbox" /> 未识别到原页码时允许按模板新增</label>`;els.pageNumberSlotGrid.appendChild(card);const ui=pageNumberSlotEls(slot);ui.use.onclick=()=>beginPageNumberBoxSelect(slot);ui.clear.onclick=()=>clearPageNumberTemplate(slot);ui.format.onchange=()=>applyPageNumberPreset(slot);ui.custom.onchange=()=>updatePageNumberCustom(slot);if(ui.role)ui.role.onchange=()=>{syncPageNumberRole(slot);renderPageNumberTemplateSlots();updatePageNumberSummary();};[ui.rangeFrom,ui.rangeTo,ui.allowAdd].forEach(x=>x&&x.addEventListener('change',()=>invalidatePageNumberScan('页码位置适用范围已变化，请重新扫描。')));card.querySelector('.remove-dynamic-slot').onclick=()=>{delete state.pageNumberTemplates[slot];for(const k of Object.keys(state.pageNumberPageOverrides))if(k.endsWith(`:${slot}`))delete state.pageNumberPageOverrides[k];card.remove();invalidatePageNumberScan('页码位置已删除，请重新扫描。');};renderPageNumberTemplateSlots();}
function pageNumberSlotRangeConfig(slot){const ui=pageNumberSlotEls(slot),global=pageNumberRange(),t=state.pageNumberTemplates[slot]||{};let from=Number(ui.rangeFrom?.value||t.applyFrom||global.from),to=Number(ui.rangeTo?.value||t.applyTo||global.to);from=Math.max(global.from,Math.min(global.to,Math.round(from||global.from)));to=Math.max(from,Math.min(global.to,Math.round(to||global.to)));if(ui.rangeFrom){ui.rangeFrom.min=global.from;ui.rangeFrom.max=global.to;ui.rangeFrom.value=from;}if(ui.rangeTo){ui.rangeTo.min=global.from;ui.rangeTo.max=global.to;ui.rangeTo.value=to;}return {from,to,allowBlankAdd:!!ui.allowAdd?.checked};}
renderPageNumberTemplateSlots=function(){for(const slot of pageNumberSlots()){const t=state.pageNumberTemplates[slot],ui=pageNumberSlotEls(slot);if(!ui.state)continue;if(ui.rangeFrom){ui.rangeFrom.max=state.pageCount||1;if(!ui.rangeFrom.value)ui.rangeFrom.value=Math.max(1,+els.pageNumberFrom?.value||1);}if(ui.rangeTo){ui.rangeTo.max=state.pageCount||1;if(!ui.rangeTo.value)ui.rangeTo.value=Math.max(1,+els.pageNumberTo?.value||state.pageCount||1);}if(t){const roles=pageNumberRoleSummary(t),cfg=pageNumberSlotRangeConfig(slot);ui.state.innerHTML=`<strong>已框选 · PDF 第 ${t.sourcePage+1} 页 · 适用 ${cfg.from}-${cfg.to}</strong><span>${escapeHtml(t.sourceText||'当前页为空白区域')} · ${t.engine==='scan'?'扫描页':'电子页'}</span>${roles?`<em>${escapeHtml(roles)}</em>`:'<em>未识别到数字，可手动选择显示格式</em>'}`;if(ui.format&&document.activeElement!==ui.format)ui.format.value=t.preset||'custom';if(ui.custom&&document.activeElement!==ui.custom)ui.custom.value=t.format||'{current}';if(ui.allowAdd&&document.activeElement!==ui.allowAdd)ui.allowAdd.checked=!!t.allowBlankAdd;ui.clear.disabled=false;}else{ui.state.innerHTML='<span>未设置 · 点击“框选位置”后在页面拖框</span>';if(ui.format)ui.format.value='current';if(ui.custom)ui.custom.value='{current}';ui.clear.disabled=true;}if(ui.use)ui.use.disabled=!state.id;}};
activePageNumberTemplates=function(){const out=[];for(const slot of pageNumberSlots()){const t=state.pageNumberTemplates[slot];if(!t)continue;const format=currentPageNumberFormat(slot);if(!pageNumberRoles(format).length)continue;const cfg=pageNumberSlotRangeConfig(slot);t.applyFrom=cfg.from;t.applyTo=cfg.to;t.allowBlankAdd=cfg.allowBlankAdd;out.push({...t,format,...cfg});}return out;};
updatePageNumberSummary=function(){if(!els.pageNumberFrom)return;const {from,to}=pageNumberRange(),start=+els.pageNumberStart.value||1,end=start+(to-from);els.pageNumberEnd.value=end;const total=pageNumberTotal(),active=pageNumberSlots().filter(s=>state.pageNumberTemplates[s]),previews=active.map(slot=>{const fmt=currentPageNumberFormat(slot),first=formatPageNumber(fmt,{current:start,total,pdfpage:from}),last=formatPageNumber(fmt,{current:end,total,pdfpage:to});return `${slot}：${first}${from===to?'':` → ${last}`}`;});els.pageNumberPreviewSummary.textContent=`PDF 第 ${from}-${to} 页 · 编号 ${start}-${end} · 总页数 ${total}${previews.length?' · '+previews.join('；'):''}`;};
pageNumberTemplateConflict=function(templates){for(let i=0;i<(templates||[]).length;i++)for(let j=i+1;j<templates.length;j++){const a=templates[i],b=templates[j],rangeOverlap=Math.max(a.from||1,b.from||1)<=Math.min(a.to||state.pageCount,b.to||state.pageCount);if(!rangeOverlap)continue;const ratio=bboxOverlapRatio(a.bbox,b.bbox);if(ratio>.30)return `位置 ${a.slot} 与 ${b.slot} 在适用页范围内重叠 ${Math.round(ratio*100)}%，请调整范围或重新框选。`;}return null;};
openPageNumberModal=function(){V2321_OPEN_PAGE_NUMBER_MODAL();const global=pageNumberRange();for(const slot of pageNumberSlots()){const ui=pageNumberSlotEls(slot);if(!state.pageNumberTemplates[slot]){if(ui.rangeFrom)ui.rangeFrom.value=global.from;if(ui.rangeTo)ui.rangeTo.value=global.to;}else{if(ui.rangeFrom&&!ui.rangeFrom.value)ui.rangeFrom.value=state.pageNumberTemplates[slot].applyFrom||global.from;if(ui.rangeTo&&!ui.rangeTo.value)ui.rangeTo.value=state.pageNumberTemplates[slot].applyTo||global.to;}}renderPageNumberTemplateSlots();updatePageNumberSummary();if(!activePageNumberTemplates().length)els.pageNumberStatus.textContent='请先框选任意页码位置；默认 A / B，也可以继续添加更多位置。';els.pageNumberTrial.disabled=!state.pageNumberScanResults.length;if(els.pageNumberUndoBatch)els.pageNumberUndoBatch.disabled=!state.lastPageNumberBatch;};
renderPageNumberResults=function(){V2321_RENDER_PAGE_NUMBER_RESULTS();if(!state.pageNumberAnomalyOnly)return;[...els.pageNumberResults.children].forEach((row,i)=>{const r=state.pageNumberScanResults[i],bad=(r?.slots||[]).some(pageNumberResultIsBad);row.style.display=bad?'':'none';});};

// v2.3.21 event wiring / overrides
if(els.selectionMode)els.selectionMode.onchange=()=>{state.selectionMode=els.selectionMode.value;state.cycleSig='';renderOverlays();if(state.selectionMode==='text')toast('只选文字：图片不会拦截点击');else if(state.selectionMode==='image')toast('只选图片');else if(state.selectionMode==='manual')toast('任意框选：拖框后只按你指定的范围识别；识别不到会自动变为新增文字块');else if(state.selectionMode==='manual-add')toast('框选新增文字：直接在空白或任意位置创建可移动文字块');else toast('智能选择：文字优先；Alt+单击可循环重叠对象');};
// Existing page mouse-down handler checks only "manual"; add manual-add by temporarily mapping it during pointer start.
els.pageWrap.addEventListener('pointerdown',e=>{if(state.cleanPreview||e.button!==0||state.pageNumberBoxSlot||state.selectionMode!=='manual-add')return;if(state.manualSelecting)return;const p=manualPoint(e);state.manualSelecting=true;state.manualSelectionRect=[p[0],p[1],p[0],p[1]];drawManualRect(state.manualSelectionRect);e.preventDefault();},true);
if(els.snapToggle)els.snapToggle.onclick=()=>{state.snapEnabled=!state.snapEnabled;els.snapToggle.textContent=`吸附：${state.snapEnabled?'开':'关'}`;els.snapToggle.classList.toggle('active',state.snapEnabled);};
if(els.objectLayerToggle)els.objectLayerToggle.onclick=()=>toggleObjectLayer();if(els.objectLayerClose)els.objectLayerClose.onclick=()=>toggleObjectLayer(false);if(els.objectLayerEditedOnly)els.objectLayerEditedOnly.onclick=()=>{state.objectLayerAll=false;els.objectLayerEditedOnly.classList.add('active');els.objectLayerAll.classList.remove('active');renderObjectLayer();};if(els.objectLayerAll)els.objectLayerAll.onclick=()=>{state.objectLayerAll=true;els.objectLayerAll.classList.add('active');els.objectLayerEditedOnly.classList.remove('active');renderObjectLayer();};
[els.blockX,els.blockY,els.blockW,els.blockH].filter(Boolean).forEach(x=>x.addEventListener('change',()=>{const r=geometryInputRect();if(r)commitSelectedRect(r,{history:true,preview:true,label:'精确调整字块坐标'});}));
if(els.objectLockBtn)els.objectLockBtn.onclick=toggleSelectedLock;if(els.reRecognizeBlock)els.reRecognizeBlock.onclick=reRecognizeSelectedBlock;if(els.convertFreeText)els.convertFreeText.onclick=convertSelectedToFreeText;if(els.resetBlockPosition)els.resetBlockPosition.onclick=resetSelectedBlockPosition;if(els.openDetailEditor)els.openDetailEditor.onclick=openDetailEditor;if(els.saveFinishedBlock)els.saveFinishedBlock.onclick=saveSelectedFinishedBlock;if(els.pasteFinishedBlock)els.pasteFinishedBlock.onclick=pasteFinishedBlockAsFree;
if(els.detailEditorClose)els.detailEditorClose.onclick=closeDetailEditor;if(els.detailEditorDone)els.detailEditorDone.onclick=closeDetailEditor;document.querySelectorAll('[data-detail-zoom]').forEach(b=>b.onclick=()=>{state.detailZoom=+b.dataset.detailZoom||4;document.querySelectorAll('[data-detail-zoom]').forEach(x=>x.classList.toggle('active',x===b));renderDetailEditor();});
if(els.batchTrial)els.batchTrial.onclick=trialBatchEdits;if(els.pageNumberAddSlot)els.pageNumberAddSlot.onclick=addPageNumberSlot;if(els.pageNumberTrial)els.pageNumberTrial.onclick=trialPageNumbers;if(els.pageNumberAnomaly)els.pageNumberAnomaly.onclick=()=>{state.pageNumberAnomalyOnly=!state.pageNumberAnomalyOnly;els.pageNumberAnomaly.textContent=state.pageNumberAnomalyOnly?'显示全部页':'只看异常页';els.pageNumberAnomaly.classList.toggle('active',state.pageNumberAnomalyOnly);renderPageNumberResults();};if(els.pageNumberUndoBatch)els.pageNumberUndoBatch.onclick=()=>undoLastPageNumberBatch();[els.pageNumberRangeFromA,els.pageNumberRangeToA,els.pageNumberAllowAddA,els.pageNumberRangeFromB,els.pageNumberRangeToB,els.pageNumberAllowAddB].filter(Boolean).forEach(x=>x.addEventListener('change',()=>invalidatePageNumberScan('页码位置适用范围或新增策略已变化，请重新扫描。')));
if(els.pageNumberBtn)els.pageNumberBtn.onclick=openPageNumberModal;

// Locked objects are not deleted accidentally.
const V2321_OPEN_DELETE_MODAL=openDeleteModal;openDeleteModal=function(){if(selectedIsLocked())return toast('当前对象已锁定，请先解锁');const e=selectedStoredEdit();if(!e&&state.selected?.item?.freeText){clearProps();renderOverlays();toast('已取消尚未运行的新增文字块');return;}if(e&&['free-text','page-number-add','page-number-replace'].includes(e.type)){pushHistory(e.type==='free-text'?'删除可移动字块':'删除页码字块',{page:state.currentPage+1,detail:e.newText||e.text||''});state.edits.delete(state.selected.key);state.feasibility.delete(state.selected.key);clearProps();updateChangeCount();renderOverlays();renderPageNumberResults();schedulePreview(0);toast('已删除当前字块');return;}return V2321_OPEN_DELETE_MODAL();};if(els.deleteTextBtn)els.deleteTextBtn.onclick=openDeleteModal;

// Keyboard movement: 1 pt, Shift 5 pt, Alt 0.1 pt.  Capture phase prevents page shortcuts from consuming it.
window.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)||!selectedBlockRect()||selectedIsLocked()||['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;const step=e.altKey?.1:(e.shiftKey?5:1),r=selectedBlockRect();let dx=0,dy=0;if(e.key==='ArrowLeft')dx=-step;if(e.key==='ArrowRight')dx=step;if(e.key==='ArrowUp')dy=-step;if(e.key==='ArrowDown')dy=step;e.preventDefault();e.stopImmediatePropagation();commitSelectedRect([r[0]+dx,r[1]+dy,r[2]+dx,r[3]+dy],{history:true,preview:true,label:'键盘微调字块'});},{capture:true});

renderFinishedBlockLibrary();

// Keep trial buttons synchronized with the latest page-number scan result.
if(els.pageNumberScan){const _v2321PnScanClick=els.pageNumberScan.onclick;els.pageNumberScan.onclick=async e=>{await _v2321PnScanClick?.call(els.pageNumberScan,e);if(els.pageNumberTrial)els.pageNumberTrial.disabled=!state.pageNumberScanResults.length;const bad=state.pageNumberScanResults.some(r=>(r.slots||[]).some(pageNumberResultIsBad));if(els.pageNumberAnomaly)els.pageNumberAnomaly.disabled=!bad;if(els.pageNumberUndoBatch)els.pageNumberUndoBatch.disabled=!state.lastPageNumberBatch;};}

// ---------- v2.3.24 reversible change log + page-number manual takeover ----------
function revisionEntries(){
  return [...state.edits.entries()].map(([key,e])=>({key,e})).sort((a,b)=>(a.e.page-b.e.page)||String(a.e.type).localeCompare(String(b.e.type))||String(a.key).localeCompare(String(b.key)));
}
function editDisplayTitle(e){
  if(!e)return '修改';
  if(e.pageNumberSlot){
    const role=e.pageNumberRole?` · ${PAGE_NUMBER_ROLE_LABELS[e.pageNumberRole]||e.pageNumberRole}`:'';
    return `页码${role}`;
  }
  if(e.type==='free-text')return '自由文字';
  if(e.type==='page-number-add')return '新增页码';
  if(e.type==='page-number-replace')return '页码原位修改';
  if(e.action==='delete')return e.type==='text'?'删除文字':'删除图片';
  return e.type==='text'?'文字修订':'图片替换';
}
function editDisplayDetail(e){
  if(!e)return '';
  if(e.type==='free-text'||e.type==='page-number-add')return `<div class="change-log-diff"><span>新增</span><code>${escapeHtml(e.text||e.newText||'')}</code></div>`;
  if(e.pageNumberSlot||e.type==='page-number-replace')return `<div class="change-log-diff"><span>原</span><code>${escapeHtml(e.oldText||'')}</code><span>新</span><code>${escapeHtml(e.newText||e.text||'')}</code></div>`;
  if(e.action==='delete')return `<div class="change-log-diff"><span>操作</span><code>${e.type==='text'?`删除：${escapeHtml(e.oldText||'文字')}`:'删除图片'}</code></div>`;
  if(e.type==='text')return `<div class="change-log-diff"><span>原</span><code>${escapeHtml(e.oldText||'')}</code><span>新</span><code>${escapeHtml(e.newText||'')}</code></div>`;
  return '<div class="change-log-diff"><span>操作</span><code>原位替换图片</code></div>';
}
function snapshotMap(s){try{return new Map(JSON.parse(s||'[]'));}catch{return new Map();}}
function earliestHistoryIndexForEditKey(key){
  for(let i=0;i<state.versionHistory.length;i++)if(snapshotMap(state.versionHistory[i].snapshot).has(key))return i;
  return -1;
}
function historyBeforeEditKey(key){
  const idx=earliestHistoryIndexForEditKey(key);if(idx<0)return state.versionHistory[0]||null;
  return idx>0?state.versionHistory[idx-1]:null;
}
function syncChangeLogSelectionButtons(){
  if(!(state.changeLogSelectedKeys instanceof Set))state.changeLogSelectedKeys=new Set();
  for(const k of [...state.changeLogSelectedKeys])if(!state.edits.has(k))state.changeLogSelectedKeys.delete(k);
  const count=state.changeLogSelectedKeys.size;
  if(els.changeLogUndoSelected){els.changeLogUndoSelected.disabled=!count;els.changeLogUndoSelected.textContent=count?`撤销选中修改（${count}）`:'撤销选中修改';}
  if(els.changeLogRestoreBeforeSelected){els.changeLogRestoreBeforeSelected.disabled=count!==1;els.changeLogRestoreBeforeSelected.title=count===1?'恢复整份文档到该修改首次出现之前':'仅选择一条修改时可用';}
}
renderChangeLog=function(){
  const rows=revisionEntries(),pages=new Set(rows.map(x=>x.e.page));
  if(els.changeLogSummary)els.changeLogSummary.textContent=rows.length?`${rows.length} 处修订 · ${pages.size} 页 · 可逐项撤销或恢复到修改前`:'当前没有修改';
  if(!els.changeLogList)return;
  if(!(state.changeLogSelectedKeys instanceof Set))state.changeLogSelectedKeys=new Set();
  for(const k of [...state.changeLogSelectedKeys])if(!state.edits.has(k))state.changeLogSelectedKeys.delete(k);
  if(!rows.length){els.changeLogList.innerHTML='<div class="change-log-empty">当前没有修改。可以关闭清单继续编辑。</div>';syncChangeLogSelectionButtons();return;}
  els.changeLogList.innerHTML=rows.map(({key,e},i)=>{
    const selected=state.changeLogSelectedKeys.has(key),firstIdx=earliestHistoryIndexForEditKey(key),first=firstIdx>=0?state.versionHistory[firstIdx]:null;
    return `<article class="change-log-item v2322${selected?' selected':''}" data-edit-key="${escapeHtml(key)}"><div class="change-log-index"><input class="change-log-select" type="checkbox" ${selected?'checked':''} aria-label="选择第 ${i+1} 项修改"><span>${i+1}</span></div><div class="change-log-main"><strong>第 ${e.page+1} 页 · ${escapeHtml(editDisplayTitle(e))}</strong>${editDisplayDetail(e)}${first?`<small class="change-log-history-ref">首次记录：历史 #${first.id} · ${formatHistoryTime(first.time)}</small>`:''}</div><div class="change-log-row-actions"><button type="button" class="mini-btn soft-btn change-log-locate" data-edit-key="${escapeHtml(key)}">定位</button><button type="button" class="mini-btn soft-btn danger change-log-undo-one" data-edit-key="${escapeHtml(key)}">撤销此项</button><button type="button" class="mini-btn soft-btn change-log-before" data-edit-key="${escapeHtml(key)}">回到此项前</button></div></article>`;
  }).join('');
  els.changeLogList.querySelectorAll('.change-log-select').forEach(cb=>cb.onchange=()=>{const row=cb.closest('[data-edit-key]'),key=row?.dataset.editKey;if(!key)return;if(cb.checked)state.changeLogSelectedKeys.add(key);else state.changeLogSelectedKeys.delete(key);row.classList.toggle('selected',cb.checked);syncChangeLogSelectionButtons();});
  els.changeLogList.querySelectorAll('.change-log-locate').forEach(b=>b.onclick=()=>locateRevisionEdit(b.dataset.editKey));
  els.changeLogList.querySelectorAll('.change-log-undo-one').forEach(b=>b.onclick=()=>deleteRevisionEditByKey(b.dataset.editKey));
  els.changeLogList.querySelectorAll('.change-log-before').forEach(b=>b.onclick=()=>restoreBeforeRevisionEdit(b.dataset.editKey));
  syncChangeLogSelectionButtons();
};
const V2322_OPEN_CHANGE_LOG=openChangeLog;
openChangeLog=function(forExport=false){if(!(state.changeLogSelectedKeys instanceof Set))state.changeLogSelectedKeys=new Set();state.changeLogSelectedKeys.clear();V2322_OPEN_CHANGE_LOG(forExport);syncChangeLogSelectionButtons();};
async function locateRevisionEdit(key){
  const e=state.edits.get(key);if(!e)return toast('该修改已经不存在');closeChangeLog();if(state.currentPage!==e.page)await loadPage(e.page);
  const current=state.edits.get(key);if(!current)return;
  if(current.type==='image')selectObject('image',{id:current.id,bbox:current.bbox,pdfBbox:current.pdfBbox||current.bbox},key);else selectEditFromLayer(key,current);
  renderOverlays();toast(`已定位到第 ${e.page+1} 页 · ${editDisplayTitle(e)}`);
}
function removeEditKeys(keys,label='撤销修改'){
  const valid=keys.filter(k=>state.edits.has(k));if(!valid.length)return 0;
  pushHistory(label,{page:(state.edits.get(valid[0])?.page??state.currentPage)+1,detail:`${valid.length} 项`});
  for(const key of valid){state.edits.delete(key);state.feasibility.delete(key);state.changeLogSelectedKeys?.delete(key);}
  if(state.selected&&valid.includes(state.selected.key))clearProps();updateChangeCount();renderOverlays();renderObjectLayer();renderPageNumberResults();renderChangeLog();schedulePreview(0);return valid.length;
}
function deleteRevisionEditByKey(key){
  const e=state.edits.get(key);if(!e)return toast('该修改已经不存在');if(e.locked&&!confirm('该对象已锁定。仍要撤销此修改并恢复原区域吗？'))return;
  const n=removeEditKeys([key],`撤销修改：第 ${e.page+1} 页 · ${editDisplayTitle(e)}`);if(n)toast('已撤销此项修改，原区域已恢复');
}
function undoSelectedChangeLogEdits(){
  const keys=[...(state.changeLogSelectedKeys||[])].filter(k=>state.edits.has(k));if(!keys.length)return toast('请先勾选要撤销的修改');
  if(!confirm(`确认撤销选中的 ${keys.length} 项修改？这些位置会恢复到原 PDF 内容。`))return;
  const n=removeEditKeys(keys,`撤销修改清单选中项（${keys.length}）`);if(n)toast(`已撤销 ${n} 项修改，原区域已恢复`,4200);
}
async function restoreBeforeRevisionEdit(key){
  const e=state.edits.get(key);if(!e)return toast('该修改已经不存在');const before=historyBeforeEditKey(key);if(!before)return toast('没有找到该修改之前的历史节点');
  if(!confirm(`将整份文档恢复到历史 #${before.id}（该修改首次出现之前）。\n该修改之后的其他修改也会一起回退。是否继续？`))return;
  const current=snapshot();state.undo.push(current);if(state.undo.length>80)state.undo.shift();state.redo=[];restoreSnapshot(before.snapshot);captureVersion(`回到修改前：第 ${e.page+1} 页 · ${editDisplayTitle(e)}`,{page:e.page+1,detail:`来自历史 #${before.id}`,sourceVersionId:before.id},true);state.changeLogSelectedKeys.clear();closeChangeLog();if(state.currentPage!==e.page)await loadPage(e.page);else await refreshPreview();toast(`已恢复到历史 #${before.id}，该项及其后的修改已回退`,5200);
}
function restoreBeforeSelectedChangeLogEdit(){const keys=[...(state.changeLogSelectedKeys||[])].filter(k=>state.edits.has(k));if(keys.length!==1)return toast('请选择且只选择一条修改');restoreBeforeRevisionEdit(keys[0]);}
if(els.changeLogUndoSelected)els.changeLogUndoSelected.onclick=undoSelectedChangeLogEdits;
if(els.changeLogRestoreBeforeSelected)els.changeLogRestoreBeforeSelected.onclick=restoreBeforeSelectedChangeLogEdit;

// Every page-number edit, including scan edits stored as ordinary `text`, is a first-class generated object.
const V2322_EDIT_IS_MOVABLE=editIsMovable;
editIsMovable=function(e){return !!e?.pageNumberSlot||V2322_EDIT_IS_MOVABLE(e);};
const V2322_EDIT_OVERLAY_ITEM=editOverlayItem;
editOverlayItem=function(e,key){
  if(e?.pageNumberSlot){const b=(e.outputBbox||e.bbox||[]).map(Number);return {id:e.id,engine:e.engine||'electronic',text:String(e.newText||e.text||e.oldText||''),bbox:[...b],tokenBbox:e.bbox||b,origin:e.origin||[b[0]||0,b[3]||0],size:e.size||Math.max(6,(b[3]||0)-(b[1]||0)),color:e.color||'#000000',font:e.font||'',manualSelection:false,freeText:false,pageNumberGenerated:true,_editKey:key,_editType:e.type,locked:!!e.locked,originalBbox:e.templateBbox||e.bbox,pageNumberSlot:e.pageNumberSlot,pageNumberRole:e.pageNumberRole};}
  return V2322_EDIT_OVERLAY_ITEM(e,key);
};
addEditOverlays=function(){
  for(const [key,e] of state.edits.entries()){
    const generated=!!e.pageNumberSlot||['free-text','page-number-add','page-number-replace'].includes(e.type);if(e.page!==state.currentPage||!generated)continue;
    const b=(e.outputBbox||e.bbox||[]).map(Number);if(b.length!==4)continue;const box=document.createElement('div');box.className='obj-box text-box edited generated-edit'+(e.pageNumberSlot?' page-number-generated':'')+(key===state.selected?.key?' selected':'');Object.assign(box.style,{left:`${toPx(b[0])}px`,top:`${toPx(b[1])}px`,width:`${Math.max(3,toPx(b[2]-b[0]))}px`,height:`${Math.max(4,toPx(b[3]-b[1]))}px`});const role=e.pageNumberRole?` · ${PAGE_NUMBER_ROLE_LABELS[e.pageNumberRole]||e.pageNumberRole}`:'';box.title=e.pageNumberSlot?`页码 ${e.pageNumberSlot}${role}：${e.newText||e.text||''} · 单击后可修改、移动或恢复原区域`:`新增文字：${e.newText||e.text||''} · 单击可选中`;box.dataset.editKey=key;box.onpointerdown=ev=>{if(state.cleanPreview)return;ev.preventDefault();ev.stopPropagation();selectEditFromLayer(key,e);};els.overlayLayer.appendChild(box);
  }
};
const V2322_SHOW_SELECTED_PROPS=showSelectedProps;
showSelectedProps=function(){
  V2322_SHOW_SELECTED_PROPS();const e=selectedStoredEdit();if(!e?.pageNumberSlot)return;
  const role=e.pageNumberRole?PAGE_NUMBER_ROLE_LABELS[e.pageNumberRole]||e.pageNumberRole:'整组';els.objectType.textContent=`页码字块 ${e.pageNumberSlot} · ${role}`;els.textContent.value=String(e.newText||e.text||'');els.fontSize.value=e.size||state.selected?.item?.size||10;els.fontColor.value=e.color||'#000000';els.fontName.value=e.font||'页码';[els.fontSize,els.fontColor].forEach(x=>x.disabled=false);[els.textX,els.textY].forEach(x=>x.disabled=true);els.scanTuneSection?.classList.toggle('hidden',String(e.engine)!=='scan');if(e.engine==='scan')loadScanVisualAdjust(e.visualAdjust);const mode=e.type==='text'?(e.engine==='scan'?'scanrevision':'stream'):e.type;renderFeasibilityStatus(state.feasibility.get(state.selected.key)||{mode,visualVerified:true,reason:'批量页码生成对象，可人工修改、移动或删除'});updateGeometryInputs();markRunPending();if(els.resetTextBtn)els.resetTextBtn.title='删除这一项页码修改并恢复原 PDF 区域';if(els.deleteTextBtn)els.deleteTextBtn.title='删除这一项页码修改并恢复原 PDF 区域';
};
const V2322_BUILD_TEXT_EDIT=buildTextEdit;
buildTextEdit=function(item){
  const stored=state.selected?state.edits.get(state.selected.key):null;if(stored?.pageNumberSlot){const size=+els.fontSize.value||stored.size||item?.size||10,color=els.fontColor.value||stored.color||'#000000',next=String(els.textContent.value??stored.newText??stored.text??'');const edit={...stored,newText:next,text:next,size,color};if(stored.type==='text'){edit.sameStyle=Math.abs(size-(stored.size||size))<.001&&String(color).toLowerCase()===String(stored.color||color).toLowerCase();edit.x=stored.x??stored.origin?.[0]??stored.bbox?.[0];edit.y=stored.y??stored.origin?.[1]??stored.bbox?.[3];}if(edit.engine==='scan')edit.visualAdjust=readScanVisualAdjust();return edit;}return V2322_BUILD_TEXT_EDIT(item);
};
const V2322_COMMIT_SELECTED_RECT=commitSelectedRect;
commitSelectedRect=function(rect,opts={}){
  const e=selectedStoredEdit();if(e?.pageNumberSlot&&e.type==='text'){
    if(!state.selected||selectedIsLocked())return false;rect=clampRectToPage(rect);if(opts.history!==false)pushHistory(opts.label||'移动 / 调整页码字块',{page:state.currentPage+1,detail:String(e.newText||'')});const base=(e.bbox||[]).map(Number),originY=Number(e.origin?.[1]??base[3]??0)-Number(base[1]??0),converted={...e,type:'page-number-replace',outputBbox:[...rect],text:String(e.newText||''),templateBbox:e.templateBbox||[...base],anchor:'center',tightNumeric:!!e.pageNumberRole,originOffsetY:Number.isFinite(originY)&&originY>0?originY:Math.max(1,(base[3]-base[1])*.82)};state.edits.set(state.selected.key,converted);state.feasibility.delete(state.selected.key);state.selected.item=editOverlayItem(converted,state.selected.key);updateGeometryInputs();renderOverlays();renderObjectLayer();updateChangeCount();if(opts.preview!==false)schedulePreview(0);showSelectedProps();return true;
  }
  return V2322_COMMIT_SELECTED_RECT(rect,opts);
};
const V2322_OPEN_DELETE_MODAL=openDeleteModal;
openDeleteModal=function(){
  const e=selectedStoredEdit();if(e?.pageNumberSlot){if(selectedIsLocked())return toast('当前页码对象已锁定，请先解锁');pushHistory(`撤销页码修改：${e.newText||e.text||''}`,{page:e.page+1,detail:`位置 ${e.pageNumberSlot}`});state.edits.delete(state.selected.key);state.feasibility.delete(state.selected.key);clearProps();updateChangeCount();renderOverlays();renderPageNumberResults();renderChangeLog();schedulePreview(0);toast('已删除该页码修改并恢复原区域');return;}return V2322_OPEN_DELETE_MODAL();
};
if(els.deleteTextBtn)els.deleteTextBtn.onclick=openDeleteModal;

// Manual takeover is a workflow lock: batch page-number runs skip these page/slot pairs, while the user can still edit them.
function pageNumberTakeoverKey(page,slot){return `${Number(page)}:${String(slot)}`;}
function ensurePageNumberTakeoverSet(){if(!(state.pageNumberManualTakeovers instanceof Set))state.pageNumberManualTakeovers=new Set();return state.pageNumberManualTakeovers;}
function isPageNumberManualTakeover(page,slot){return ensurePageNumberTakeoverSet().has(pageNumberTakeoverKey(page,slot));}
function pageNumberSlotEdits(page,slot){return [...state.edits.entries()].filter(([,e])=>e.page===Number(page)&&e.pageNumberSlot===String(slot));}
const V2322_ANNOTATE_PAGE_NUMBER_ANOMALIES=annotatePageNumberAnomalies;
annotatePageNumberAnomalies=function(){for(const r of state.pageNumberScanResults||[])for(const sr of r.slots||[])sr._page=r.page;return V2322_ANNOTATE_PAGE_NUMBER_ANOMALIES();};
const V2322_PAGE_NUMBER_RESULT_IS_BAD=pageNumberResultIsBad;
pageNumberResultIsBad=function(sr){return isPageNumberManualTakeover(sr?._page,sr?.slot)||V2322_PAGE_NUMBER_RESULT_IS_BAD(sr);};
const V2322_BUILD_PAGE_NUMBER_PAGE_EDITS=buildPageNumberPageEdits;
buildPageNumberPageEdits=function(result,templates){
  const built=V2322_BUILD_PAGE_NUMBER_PAGE_EDITS(result,templates),manual=new Set((result.slots||[]).filter(sr=>isPageNumberManualTakeover(result.page,sr.slot)).map(sr=>sr.slot));if(!manual.size)return built;built.edits=(built.edits||[]).filter(e=>!manual.has(e.pageNumberSlot));built.issues=(built.issues||[]).filter(x=>!manual.has(x.slot));for(const slot of manual)built.unchanged.push({slot,role:'manual-takeover'});return built;
};
const V2322_SET_PAGE_NUMBER_RUN_STATUS=setPageNumberRunStatus;
setPageNumberRunStatus=function(page,slot,text,kind='ok'){if(isPageNumberManualTakeover(page,slot))return V2322_SET_PAGE_NUMBER_RUN_STATUS(page,slot,'人工接管 · 已跳过批量','skip');return V2322_SET_PAGE_NUMBER_RUN_STATUS(page,slot,text,kind);};
async function focusManualTakeover(page,slots){
  closePageNumberModal();if(state.currentPage!==page)await loadPage(page);state.objectLayerOpen=true;renderObjectLayer();const hits=[...state.edits.entries()].filter(([,e])=>e.page===page&&slots.includes(e.pageNumberSlot));if(hits.length){for(const [,e] of hits)e.locked=false;selectEditFromLayer(hits[0][0],hits[0][1]);renderOverlays();toast('已进入人工接管：可直接改文字、移动字块、恢复原区域或删除整个页码组',5200);}else{state.selectionMode='manual';if(els.selectionMode)els.selectionMode.value='manual';renderOverlays();toast('该页当前没有生成的页码对象。请用“任意框选”圈住需要手动修改的页码。',5200);}
}
async function takeOverPageNumberSlot(page,slot){ensurePageNumberTakeoverSet().add(pageNumberTakeoverKey(page,slot));const row=state.pageNumberScanResults.find(r=>r.page===page),sr=row?.slots?.find(x=>x.slot===slot);if(sr)sr.runStatus={text:'人工接管',kind:'skip'};renderPageNumberResults();await focusManualTakeover(page,[slot]);}
async function takeOverPageNumberPage(page){const row=state.pageNumberScanResults.find(r=>r.page===page),slots=(row?.slots||[]).map(x=>x.slot);if(!slots.length)return toast('当前页没有页码位置结果');for(const slot of slots)ensurePageNumberTakeoverSet().add(pageNumberTakeoverKey(page,slot));for(const sr of row.slots||[])sr.runStatus={text:'人工接管',kind:'skip'};renderPageNumberResults();await focusManualTakeover(page,slots);}
function releasePageNumberTakeover(page,slot){ensurePageNumberTakeoverSet().delete(pageNumberTakeoverKey(page,slot));const row=state.pageNumberScanResults.find(r=>r.page===page),sr=row?.slots?.find(x=>x.slot===slot);if(sr?.runStatus?.text?.includes('人工接管'))sr.runStatus=null;renderPageNumberResults();toast(`PDF 第 ${page+1} 页 · 位置 ${slot} 已恢复自动处理`);}
function deletePageNumberPageGenerated(page){const hits=[...state.edits.entries()].filter(([,e])=>e.page===page&&e.pageNumberSlot);if(!hits.length)return toast('这一页没有批量生成的页码对象');if(hits.some(([,e])=>e.locked)&&!confirm('本页包含锁定页码对象。是否仍然删除并恢复原区域？'))return;pushHistory('删除本页全部生成页码',{page:page+1,detail:`${hits.length} 个对象`});for(const [key] of hits){state.edits.delete(key);state.feasibility.delete(key);}if(state.selected&&hits.some(([key])=>key===state.selected.key))clearProps();updateChangeCount();renderOverlays();renderPageNumberResults();renderChangeLog();schedulePreview(0);toast(`已删除 PDF 第 ${page+1} 页全部生成页码，原区域已恢复`,4200);}
const V2322_RENDER_PAGE_NUMBER_RESULTS=renderPageNumberResults;
renderPageNumberResults=function(){
  annotatePageNumberAnomalies();V2322_RENDER_PAGE_NUMBER_RESULTS();if(!els.pageNumberResults)return;
  for(const row of els.pageNumberResults.querySelectorAll('.page-number-row-v2')){const page=Number(row.dataset.page),head=row.querySelector(':scope > strong');if(head&&!head.querySelector('.pn-page-actions')){const actions=document.createElement('span');actions.className='pn-page-actions';actions.innerHTML=`<button type="button" class="mini-btn soft-btn pn-takeover-page">手动接管本页</button><button type="button" class="mini-btn soft-btn danger pn-delete-page-generated">删除本页生成内容</button>`;head.appendChild(actions);actions.querySelector('.pn-takeover-page').onclick=e=>{e.stopPropagation();takeOverPageNumberPage(page);};actions.querySelector('.pn-delete-page-generated').onclick=e=>{e.stopPropagation();deletePageNumberPageGenerated(page);};}
    for(const slotEl of row.querySelectorAll('.pn-slot-result')){const slot=slotEl.querySelector('i')?.textContent?.trim();if(!slot)continue;const manual=isPageNumberManualTakeover(page,slot),actionBox=slotEl.querySelector('.pn-result-actions');if(!actionBox)continue;slotEl.classList.toggle('manual-takeover',manual);const oldDelete=actionBox.querySelector('.pn-delete-group');if(oldDelete)oldDelete.textContent='删除生成内容';const b=document.createElement('button');b.type='button';b.className='mini-btn soft-btn '+(manual?'pn-release-takeover':'pn-takeover-slot');b.textContent=manual?'恢复自动':'手动接管';actionBox.appendChild(b);if(manual){let badge=slotEl.querySelector('.pn-manual-badge');if(!badge){badge=document.createElement('em');badge.className='pn-run skip pn-manual-badge';badge.textContent='人工接管';slotEl.querySelector('.pn-desc')?.appendChild(badge);}b.onclick=()=>releasePageNumberTakeover(page,slot);}else b.onclick=()=>takeOverPageNumberSlot(page,slot);}
  }
};

// Keep the two new workflow states reset when a new PDF is imported.
const V2322_IMPORT_PDF=importPdf;
importPdf=async function(file){const out=await V2322_IMPORT_PDF(file);state.changeLogSelectedKeys=new Set();state.pageNumberManualTakeovers=new Set();return out;};

// ---------- v2.3.25 numeric-slot page-number workflow ----------
// Page-number OCR is only a locator. The user owns the values that get written:
// current-page = configured sequence, total-page = configured fixed value.
const V2325_PAGE_NUMBER_SLOT_ELS = pageNumberSlotEls;
pageNumberSlotEls=function(slot){
  const ui=V2325_PAGE_NUMBER_SLOT_ELS(slot),card=els.pageNumberSlotGrid?.querySelector(`[data-slot="${slot}"]`);
  ui.role=slot==='A'?document.querySelector('#pageNumberRoleA'):slot==='B'?document.querySelector('#pageNumberRoleB'):card?.querySelector('.slot-role');
  return ui;
};
function pageNumberRoleMode(slot){return String(pageNumberSlotEls(slot).role?.value||state.pageNumberTemplates[slot]?.roleMode||'auto');}
function resolvedPageNumberRoleMode(template,slot){
  const mode=pageNumberRoleMode(slot);if(mode!=='auto')return mode;
  const roles=pageNumberRoles(template?.format||inferPageNumberTemplate(template?.sourceText||'').format);
  return roles.includes('current')&&roles.includes('total')?'both':roles.includes('total')?'total':'current';
}
function pageNumberEditRoles(template,slot){const mode=resolvedPageNumberRoleMode(template,slot);return mode==='both'?['current','total']:[mode==='total'?'total':'current'];}
function syncPageNumberRole(slot,{invalidate=true}={}){
  const t=state.pageNumberTemplates[slot];if(!t)return;
  const ui=pageNumberSlotEls(slot),mode=pageNumberRoleMode(slot),inferred=inferPageNumberTemplate(t.sourceText||'');let fmt=inferred.format||'{current}';
  if(mode==='current'&&pageNumberRoles(fmt).length===1)fmt=fmt.replace(/\{(?:total|pdfpage)\}/g,'{current}');
  if(mode==='total'&&pageNumberRoles(fmt).length===1)fmt=fmt.replace(/\{(?:current|pdfpage)\}/g,'{total}');
  if(mode==='both'&&!pageNumberRoles(fmt).includes('total'))fmt='{current}/{total}';
  t.roleMode=mode;t.format=fmt;t.preset=Object.entries(PAGE_NUMBER_PRESETS).find(([,v])=>v===fmt)?.[0]||'custom';t.editRoles=pageNumberEditRoles(t,slot);
  if(ui.custom)ui.custom.value=fmt;if(ui.format)ui.format.value=t.preset;if(ui.role&&document.activeElement!==ui.role)ui.role.value=mode;
  if(invalidate)invalidatePageNumberScan('数字槽角色已变化，请重新识别原页码数字。');
}
const V2325_STORE_PAGE_NUMBER_BOX_TEMPLATE=storePageNumberBoxTemplate;
storePageNumberBoxTemplate=function(slot,field,selectionBbox,pageMeta={}){const ok=V2325_STORE_PAGE_NUMBER_BOX_TEMPLATE(slot,field,selectionBbox,pageMeta);if(ok){syncPageNumberRole(slot,{invalidate:false});renderPageNumberTemplateSlots();invalidatePageNumberScan('页码数字模板已更新，请重新识别。');}return ok;};

const V2325_RENDER_PAGE_NUMBER_TEMPLATE_SLOTS=renderPageNumberTemplateSlots;
renderPageNumberTemplateSlots=function(){
  V2325_RENDER_PAGE_NUMBER_TEMPLATE_SLOTS();
  for(const slot of pageNumberSlots()){
    const t=state.pageNumberTemplates[slot],ui=pageNumberSlotEls(slot);if(ui.role){ui.role.disabled=!t;ui.role.value=t?.roleMode||'auto';}
    if(!t||!ui.state)continue;const mode=resolvedPageNumberRoleMode(t,slot),label=mode==='both'?'当前页 + 总页数':mode==='total'?'只改“共几页”':'只改“第几页”';
    const detected=(t.numberGroups||[]).map((g,i)=>`数字${i+1}=${g.text||'—'}`).join(' · ');
    ui.state.innerHTML=`<strong>已框选 · PDF 第 ${t.sourcePage+1} 页 · ${label}</strong><span>${escapeHtml(t.sourceText||'未识别到文字')} · ${t.engine==='scan'?'扫描页':'电子页'}</span>${detected?`<em>识别：${escapeHtml(detected)}</em>`:'<em>未识别到数字，请重新框选</em>'}`;
  }
};

const V2325_ACTIVE_PAGE_NUMBER_TEMPLATES=activePageNumberTemplates;
activePageNumberTemplates=function(){return V2325_ACTIVE_PAGE_NUMBER_TEMPLATES().map(t=>({...t,roleMode:pageNumberRoleMode(t.slot),editRoles:pageNumberEditRoles(t,t.slot)}));};

const pageNumberStepEl=document.querySelector('#pageNumberStep');
pageNumberTotal=function(){const total=Math.max(1,Math.round(+els.pageNumberTotalValue.value||1));els.pageNumberTotalValue.disabled=false;els.pageNumberTotalValue.value=total;if(els.pageNumberTotalMode)els.pageNumberTotalMode.value='manual';return total;};
pageNumberValuesForPage=function(page){const {from}=pageNumberRange(),start=Math.round(+els.pageNumberStart.value||1),step=Math.round(+pageNumberStepEl?.value||1)||1,total=pageNumberTotal();return {current:start+(page+1-from)*step,total,pdfpage:page+1};};
updatePageNumberSummary=function(){
  if(!els.pageNumberFrom)return;const {from,to}=pageNumberRange(),start=Math.round(+els.pageNumberStart.value||1),step=Math.round(+pageNumberStepEl?.value||1)||1,end=start+(to-from)*step,total=pageNumberTotal();els.pageNumberEnd.value=end;
  const active=activePageNumberTemplates(),roleText=active.length?active.map(t=>`${t.slot}:${resolvedPageNumberRoleMode(t,t.slot)==='both'?'当前+总页':resolvedPageNumberRoleMode(t,t.slot)==='total'?'总页':'当前页'}`).join(' / '):'未设置数字槽';
  if(els.pageNumberPreviewSummary)els.pageNumberPreviewSummary.textContent=`PDF 第 ${from}-${to} 页 · 当前页数字 ${start}${step===1?'→':`（步长 ${step}）→`}${end} · “共几页”固定 ${total} · ${roleText}`;
};

function pageNumberRoleForPart(part,roles,index){return part?.role||roles[index]||'current';}
const V2325_CORE_BUILD_PAGE_NUMBER_PAGE_EDITS=V2322_BUILD_PAGE_NUMBER_PAGE_EDITS;
buildPageNumberPageEdits=function(result,templates){
  const vals=pageNumberValuesForPage(result.page),edits=[],unchanged=[],issues=[];
  for(const sr of result.slots||[]){
    const t=templates.get(sr.slot);if(!t)continue;
    if(isPageNumberManualTakeover(result.page,sr.slot)){unchanged.push({slot:sr.slot,role:'manual-takeover'});continue;}
    const allRoles=pageNumberRoles(t.format),wanted=new Set(t.editRoles||pageNumberEditRoles(t,sr.slot)),parts=sr.parts||[];
    if(sr.validation){issues.push({slot:sr.slot,text:sr.validation.text});continue;}
    if(!sr.found){if(t.allowBlankAdd){issues.push({slot:sr.slot,text:'未找到原数字；数字槽模式默认不建议新增，请手动接管确认位置。'});}else issues.push({slot:sr.slot,text:'未识别到原页码数字；不会新增。'});continue;}
    if(!parts.length){issues.push({slot:sr.slot,text:'识别到页码区域，但没有取得可替换的原数字坐标；请对此页重新框选。'});continue;}
    let matchedWanted=0;
    for(let i=0;i<parts.length;i++){
      const part=parts[i],role=pageNumberRoleForPart(part,allRoles,i);if(!wanted.has(role))continue;matchedWanted++;
      const newValue=String(rolePageNumberValue(role,vals)),oldValue=String(part.oldText||'');if(oldValue===newValue){unchanged.push({slot:sr.slot,role});continue;}
      if(oldValue.length===newValue.length&&String(part.item?.engine||t.engine)==='scan')edits.push(pageNumberTextEdit(part.item,result.page,newValue,sr.slot,t,role));else edits.push(pageNumberPartReplaceEdit(part,result.page,newValue,sr.slot,t,role));
    }
    if(!matchedWanted)issues.push({slot:sr.slot,text:`已识别页码，但没有找到要修改的${[...wanted].includes('total')?'“共几页”':'“第几页”'}数字槽。`});
  }
  return {edits,unchanged,issues,vals};
};

const V2325_VALIDATE_PAGE_NUMBER_SLOT=validatePageNumberSlot;
validatePageNumberSlot=function(sr,t,page){
  if(!t)return null;if(!sr.found)return t.allowBlankAdd?null:{kind:'fail',code:'not-found',text:'未识别到原页码数字；不会新增。'};
  const parts=sr.parts||[],wanted=new Set(t.editRoles||pageNumberEditRoles(t,t.slot));if(!parts.length)return {kind:'fail',code:'geometry',text:'识别到页码区域，但未取得原数字坐标'};
  const roles=pageNumberRoles(t.format);const got=new Set(parts.map((p,i)=>pageNumberRoleForPart(p,roles,i)));for(const r of wanted)if(!got.has(r))return {kind:'fail',code:'role',text:r==='total'?'未定位到“共几页”的数字':'未定位到“第几页”的数字'};return null;
};

const V2325_RENDER_PAGE_NUMBER_RESULTS=renderPageNumberResults;
renderPageNumberResults=function(){
  if(!els.pageNumberResults)return;annotatePageNumberAnomalies();els.pageNumberResults.innerHTML='';if(!state.pageNumberScanResults.length)return;const templates=new Map(activePageNumberTemplates().map(t=>[t.slot,t]));
  for(const r of state.pageNumberScanResults){if(state.pageNumberAnomalyOnly&&!(r.slots||[]).some(pageNumberResultIsBad))continue;const vals=pageNumberValuesForPage(r.page),row=document.createElement('div');row.className='page-number-row-v2';row.dataset.page=String(r.page);const slotHtml=(r.slots||[]).map(sr=>{const t=templates.get(sr.slot);if(!t)return '';const roles=pageNumberRoles(t.format),wanted=new Set(t.editRoles||pageNumberEditRoles(t,sr.slot)),parts=sr.parts||[],status=sr.runStatus||'';let desc='';if(sr.validation)desc=`<b class="pn-anomaly-text">${escapeHtml(sr.validation.text)}</b>`;else if(sr.found){const recognized=parts.map((p,i)=>`${PAGE_NUMBER_ROLE_LABELS[pageNumberRoleForPart(p,roles,i)]||'数字'}=${escapeHtml(p.oldText||'')}`).join(' · ');const changes=parts.map((p,i)=>{const role=pageNumberRoleForPart(p,roles,i);if(!wanted.has(role))return '';return `${escapeHtml(p.oldText||'')}→${escapeHtml(String(rolePageNumberValue(role,vals)))}`;}).filter(Boolean).join('；');desc=`识别 ${recognized||escapeHtml(sr.oldText||'')} ${changes?`<b>· 原位替换 ${changes}</b>`:''} <small>固定文字不动</small>`;}else desc='<b class="pn-anomaly-text">未识别原数字，不新增</b>';if(status)desc+=`<em class="pn-run ${status.kind||''}">${escapeHtml(status.text||'')}</em>`;const generated=allEdits().some(e=>e.page===r.page&&e.pageNumberSlot===sr.slot),manual=isPageNumberManualTakeover(r.page,sr.slot);return `<span class="pn-slot-result ${sr.found?'replace':'add'} ${pageNumberResultIsBad(sr)?'anomaly':''} ${manual?'manual-takeover':''}"><i>${sr.slot}</i><span class="pn-desc">${desc}${manual?'<em class="pn-run skip">人工接管</em>':''}</span><span class="pn-result-actions"><button type="button" class="mini-btn soft-btn pn-rebox" data-page="${r.page}" data-slot="${escapeHtml(sr.slot)}">此页重定位</button>${generated?`<button type="button" class="mini-btn soft-btn danger pn-delete-group" data-page="${r.page}" data-slot="${escapeHtml(sr.slot)}">删除生成内容</button>`:''}<button type="button" class="mini-btn soft-btn ${manual?'pn-release-takeover':'pn-takeover-slot'}" data-page="${r.page}" data-slot="${escapeHtml(sr.slot)}">${manual?'恢复自动':'手动接管'}</button></span></span>`;}).join('');row.innerHTML=`<strong>PDF 第 ${r.page+1} 页 <span class="pn-page-actions"><button type="button" class="mini-btn soft-btn pn-takeover-page">手动接管本页</button><button type="button" class="mini-btn soft-btn danger pn-delete-page-generated">删除本页生成内容</button></span></strong><div>${slotHtml}</div>`;els.pageNumberResults.appendChild(row);row.querySelector('.pn-takeover-page').onclick=()=>takeOverPageNumberPage(r.page);row.querySelector('.pn-delete-page-generated').onclick=()=>deletePageNumberPageGenerated(r.page);}
  els.pageNumberResults.querySelectorAll('.pn-rebox').forEach(b=>b.onclick=()=>reboxPageNumberResult(+b.dataset.page,b.dataset.slot));els.pageNumberResults.querySelectorAll('.pn-delete-group').forEach(b=>b.onclick=()=>deletePageNumberGroup(+b.dataset.page,b.dataset.slot));els.pageNumberResults.querySelectorAll('.pn-takeover-slot').forEach(b=>b.onclick=()=>takeOverPageNumberSlot(+b.dataset.page,b.dataset.slot));els.pageNumberResults.querySelectorAll('.pn-release-takeover').forEach(b=>b.onclick=()=>releasePageNumberTakeover(+b.dataset.page,b.dataset.slot));
};

const V2325_SCAN_PAGE_NUMBERS=scanPageNumbers;
scanPageNumbers=async function(){for(const t of activePageNumberTemplates())syncPageNumberRole(t.slot,{invalidate:false});return V2325_SCAN_PAGE_NUMBERS();};
const V2325_OPEN_PAGE_NUMBER_MODAL=openPageNumberModal;
openPageNumberModal=function(){if(els.pageNumberTotalMode)els.pageNumberTotalMode.value='manual';V2325_OPEN_PAGE_NUMBER_MODAL();updatePageNumberSummary();};

const V2325_ADD_PAGE_NUMBER_SLOT=addPageNumberSlot;
addPageNumberSlot=function(){
  const before=new Set(pageNumberSlots());V2325_ADD_PAGE_NUMBER_SLOT();const slot=pageNumberSlots().find(s=>!before.has(s));if(!slot)return;const card=els.pageNumberSlotGrid?.querySelector(`[data-slot="${slot}"]`);if(!card)return;
  const stateEl=card.querySelector('.slot-state');if(stateEl&&!card.querySelector('.slot-role')){const label=document.createElement('label');label.textContent='这个框修改什么';const sel=document.createElement('select');sel.className='slot-role';sel.innerHTML='<option value="auto">自动识别</option><option value="current">只改“第几页”</option><option value="total">只改“共几页”</option><option value="both">当前页 + 总页数</option>';stateEl.insertAdjacentElement('afterend',label);label.insertAdjacentElement('afterend',sel);sel.onchange=()=>{syncPageNumberRole(slot);renderPageNumberTemplateSlots();updatePageNumberSummary();};}
  card.querySelector('.slot-format')?.classList.add('hidden');card.querySelector('.slot-custom')?.classList.add('hidden');renderPageNumberTemplateSlots();
};

for(const slot of ['A','B']){const ui=pageNumberSlotEls(slot);if(ui.role)ui.role.onchange=()=>{syncPageNumberRole(slot);renderPageNumberTemplateSlots();updatePageNumberSummary();};}
[els.pageNumberFrom,els.pageNumberTo,els.pageNumberStart,els.pageNumberTotalValue,pageNumberStepEl].filter(Boolean).forEach(x=>x.addEventListener('change',()=>{updatePageNumberSummary();invalidatePageNumberScan('数字填充值已变化，请重新识别或直接重新试运行。');}));
if(els.pageNumberTotalMode)els.pageNumberTotalMode.value='manual';

// ---------- v2.3.26 page commit / export selection / high-DPI preview ----------
Object.assign(state,{
  previewQuality:state.previewQuality||'auto',lastRenderScale:state.lastRenderScale||1.7,
  currentBaselineId:Number(state.currentBaselineId||0),baselineSeq:Number(state.baselineSeq||0),
  changeLogFilter:state.changeLogFilter||'all',changeLogTombstones:state.changeLogTombstones||[],
  exportSelectedKeys:state.exportSelectedKeys instanceof Set?state.exportSelectedKeys:new Set(),
  pageRenderStatus:state.pageRenderStatus instanceof Map?state.pageRenderStatus:new Map(),
  resolvedAnomalyPages:state.resolvedAnomalyPages instanceof Set?state.resolvedAnomalyPages:new Set()
});
Object.assign(els,{
  saveProgressBtn:$('#saveProgressBtn'),saveContinueBtn:$('#saveContinueBtn'),previewQuality:$('#previewQuality'),imageDpiInfo:$('#imageDpiInfo'),
  changeLogFilters:$('#changeLogFilters'),renderCurrentPageBtn:$('#renderCurrentPageBtn'),renderNextAnomalyBtn:$('#renderNextAnomalyBtn'),exportSelectTools:$('#exportSelectTools'),
  exportSelectAll:$('#exportSelectAll'),exportSelectNone:$('#exportSelectNone'),exportSelectInvert:$('#exportSelectInvert'),exportSelectAnomaly:$('#exportSelectAnomaly'),exportSelectCurrent:$('#exportSelectCurrent')
});

function desiredRenderScale(){
  const mode=state.previewQuality||els.previewQuality?.value||'auto',dpr=Math.max(1,Math.min(3,window.devicePixelRatio||1));
  const cssPxPerPt=Math.max(.15,(state.scale||1.7)*(state.zoom||1));
  const need=cssPxPerPt*dpr*1.08;
  if(mode==='standard')return 1.7;
  if(mode==='high')return Math.max(3,Math.min(8,need*1.55));
  return Math.max(1.25,Math.min(6.5,need));
}
function rerenderForResolution(force=false){const next=desiredRenderScale(),prev=Number(state.lastRenderScale||0);if(force||!prev||next>prev*1.16||next<prev*.72){state.lastRenderScale=next;schedulePreview(120);}}
const V2326_SET_VIEW_MODE=setViewMode;
setViewMode=function(mode){V2326_SET_VIEW_MODE(mode);rerenderForResolution();};
const V2326_RESTORE_CUSTOM_ZOOM=restoreCustomZoom;
restoreCustomZoom=function(zoom){V2326_RESTORE_CUSTOM_ZOOM(zoom);rerenderForResolution();};
if(els.previewQuality){els.previewQuality.value=state.previewQuality;els.previewQuality.onchange=()=>{state.previewQuality=els.previewQuality.value;rerenderForResolution(true);toast(`预览清晰度：${els.previewQuality.options[els.previewQuality.selectedIndex].text}`);};}

function imageDimensionsFromDataUrl(dataUrl){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve({width:im.naturalWidth||0,height:im.naturalHeight||0});im.onerror=()=>reject(new Error('无法读取图片尺寸'));im.src=dataUrl;});}
function updateImageDpiInfo(edit){
  if(!els.imageDpiInfo)return;const w=Number(edit?.sourceWidth||0),h=Number(edit?.sourceHeight||0),b=edit?.pdfBbox||edit?.bbox||state.selected?.item?.pdfBbox||state.selected?.item?.bbox;
  if(!w||!h||!b?.length){els.imageDpiInfo.classList.remove('warn');els.imageDpiInfo.textContent='选择图片后会显示原图尺寸、目标框与估算有效 DPI。';return;}
  const wp=Math.max(.1,Number(b[2])-Number(b[0])),hp=Math.max(.1,Number(b[3])-Number(b[1])),dpi=Math.round(Math.min(w/(wp/72),h/(hp/72)));
  els.imageDpiInfo.classList.toggle('warn',dpi<150);els.imageDpiInfo.textContent=`原图：${w} × ${h} px · 目标框：${wp.toFixed(1)} × ${hp.toFixed(1)} pt · 估算有效 DPI：${dpi}${dpi<150?' · ⚠ 原图分辨率偏低，导出后可能模糊':''}`;
}
const V2326_SHOW_SELECTED_PROPS=showSelectedProps;
showSelectedProps=function(){const out=V2326_SHOW_SELECTED_PROPS();if(state.selected?.type==='image')updateImageDpiInfo(state.edits.get(state.selected.key));else updateImageDpiInfo(null);return out;};

async function regionCropBlob(bbox,{scale=6,padding=0,includeEdits=true}={}){const pageEdits=includeEdits?allEdits().filter(e=>e.page===state.currentPage):[];const r=await fetch('/api/region-crop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,page:state.currentPage,bbox,scale,padding,edits:pageEdits})});if(!r.ok)throw new Error(await apiError(r));return await r.blob();}
function blobImage(blob){return new Promise((resolve,reject)=>{const url=URL.createObjectURL(blob),im=new Image();im.onload=()=>{URL.revokeObjectURL(url);resolve(im)};im.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('高清裁切加载失败'))};im.src=url;});}
async function transparentSpriteFromCrop(blob){const im=await blobImage(blob),c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(im,0,0);const img=ctx.getImageData(0,0,c.width,c.height),d=img.data,w=c.width,h=c.height,pts=[[1,1],[Math.max(0,w-2),1],[1,Math.max(0,h-2)],[Math.max(0,w-2),Math.max(0,h-2)]],bg=[0,0,0];for(const [x,y] of pts){const i=(y*w+x)*4;bg[0]+=d[i];bg[1]+=d[i+1];bg[2]+=d[i+2];}for(let j=0;j<3;j++)bg[j]/=pts.length;for(let i=0;i<d.length;i+=4){const dist=Math.sqrt((d[i]-bg[0])**2+(d[i+1]-bg[1])**2+(d[i+2]-bg[2])**2);d[i+3]=Math.max(0,Math.min(255,(dist-7)*16));}ctx.putImageData(img,0,0);return c.toDataURL('image/png');}
saveSelectedFinishedBlock=async function(){
  const edit=selectedStoredEdit();if(!state.selected||state.selected.type!=='text'||!edit)return toast('请先运行并确认一个文字修改，再保存成品字组');const rect=selectedBlockRect()||edit.bbox,text=String(edit.newText||edit.text||'').trim();if(!text)return toast('当前字块没有文字内容');
  try{const blob=await regionCropBlob(rect,{scale:6,padding:1,includeEdits:true}),sprite=await transparentSpriteFromCrop(blob),tpl={id:`block-${Date.now()}`,documentId:state.id,text,width:rect[2]-rect[0],height:rect[3]-rect[1],engine:edit.engine||'scan',font:edit.font||'',size:edit.size||10,color:edit.color||'#000000',visualAdjust:normalizeScanVisualAdjust(edit.visualAdjust),dataUrl:sprite,sourceScale:6};state.blockLibrary.set(text,tpl);state.blockClipboard=tpl;renderFinishedBlockLibrary();toast(`已从 PDF 坐标以 6× 高清裁切保存“${text}”`);}catch(e){toast(`高清成品字裁切失败：${e.message}`,5200);}
};
if(els.saveFinishedBlock)els.saveFinishedBlock.onclick=saveSelectedFinishedBlock;
let detailRenderToken=0;
renderDetailEditor=async function(){
  const rect=selectedBlockRect();if(!rect?.length||!els.detailCanvas)return;const token=++detailRenderToken,pad=Math.max(6,Math.min(20,(rect[3]-rect[1])*1.8)),pw=Number(state.pageData?.width)||1,ph=Number(state.pageData?.height)||1,crop=[Math.max(0,rect[0]-pad),Math.max(0,rect[1]-pad),Math.min(pw,rect[2]+pad),Math.min(ph,rect[3]+pad)],z=state.detailZoom||4,c=els.detailCanvas;c.width=Math.max(100,Math.round((crop[2]-crop[0])*z));c.height=Math.max(100,Math.round((crop[3]-crop[1])*z));state.detailCrop=crop;try{const blob=await regionCropBlob(crop,{scale:Math.min(8,Math.max(5,z*(window.devicePixelRatio||1))),padding:0,includeEdits:true}),im=await blobImage(blob);if(token!==detailRenderToken)return;const ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);ctx.drawImage(im,0,0,c.width,c.height);}catch(e){if(token===detailRenderToken)toast(`局部高清预览失败：${e.message}`,4200);}const o=els.detailObject;o.classList.remove('hidden');Object.assign(o.style,{left:`${(rect[0]-crop[0])*z}px`,top:`${(rect[1]-crop[1])*z}px`,width:`${Math.max(5,(rect[2]-rect[0])*z)}px`,height:`${Math.max(5,(rect[3]-rect[1])*z)}px`});els.detailEditorInfo.textContent=`${Math.round(z*100)}% · 高清 PDF crop · X ${rect[0].toFixed(1)} / Y ${rect[1].toFixed(1)}`;
};

function unresolvedPageNumberAnomaly(page){if(state.resolvedAnomalyPages?.has(page))return false;const r=(state.pageNumberScanResults||[]).find(x=>x.page===page);if(!r)return state.pageRenderStatus?.get(page)==='anomaly';return (r.slots||[]).some(sr=>{if(isPageNumberManualTakeover(page,sr.slot))return false;return !!sr.validation||!sr.found||sr.runStatus?.kind==='fail'||sr.runStatus?.kind==='error';});}
function editStatus(key,e){if(e?._status)return e._status;if(isPageNumberManualTakeover(e?.page,e?.pageNumberSlot)||e?.manualTakeover||e?.type==='free-text'||String(e?.id||'').startsWith('manual-'))return 'manual';if(unresolvedPageNumberAnomaly(e?.page))return 'anomaly';if(state.pageRenderStatus?.get(e?.page)==='anomaly')return 'anomaly';return 'success';}
function statusLabel(s){return ({success:'已成功',anomaly:'异常',manual:'人工修改',undone:'已撤销'})[s]||'已成功';}
function allChangeRows(){const active=[...state.edits.entries()].map(([key,e])=>({key,e,status:editStatus(key,e),undone:false}));const gone=(state.changeLogTombstones||[]).map((x,i)=>({key:x.key||`undone-${i}`,e:x.e||{},status:'undone',undone:true,time:x.time}));return [...active,...gone].sort((a,b)=>(a.e.page-b.e.page)||(a.undone-b.undone)||String(a.key).localeCompare(String(b.key)));}
const V2326_REMOVE_EDIT_KEYS=removeEditKeys;
removeEditKeys=function(keys,label='撤销修改'){const saved=keys.filter(k=>state.edits.has(k)).map(k=>({key:k,e:JSON.parse(JSON.stringify(state.edits.get(k))),time:Date.now()}));const n=V2326_REMOVE_EDIT_KEYS(keys,label);if(n){state.changeLogTombstones.push(...saved);if(state.changeLogTombstones.length>160)state.changeLogTombstones.splice(0,state.changeLogTombstones.length-160);renderChangeLog();}return n;};
function changeLogActiveSelection(){return state.changeLogExport?state.exportSelectedKeys:state.changeLogSelectedKeys;}
function setExportSelection(keys){state.exportSelectedKeys=new Set(keys.filter(k=>state.edits.has(k)));renderChangeLog();}
renderChangeLog=function(){
  const filter=state.changeLogFilter||'all',all=allChangeRows(),rows=filter==='all'?all:all.filter(x=>x.status===filter),activeSel=changeLogActiveSelection(),activePages=new Set([...state.edits.values()].map(e=>e.page));
  if(els.changeLogSummary){const selected=state.changeLogExport?` · 本次导出 ${state.exportSelectedKeys.size}/${state.edits.size} 项`:'';els.changeLogSummary.textContent=`${state.edits.size} 处当前修订 · ${activePages.size} 页${state.changeLogTombstones.length?` · ${state.changeLogTombstones.length} 项已撤销`:''}${selected}`;}
  els.exportSelectTools?.classList.toggle('hidden',!state.changeLogExport);els.changeLogUndoSelected?.classList.toggle('hidden',state.changeLogExport);els.changeLogRestoreBeforeSelected?.classList.toggle('hidden',state.changeLogExport);
  if(!els.changeLogList)return;if(!rows.length){els.changeLogList.innerHTML='<div class="change-log-empty">当前筛选条件下没有记录。</div>';syncChangeLogSelectionButtons();return;}
  els.changeLogList.innerHTML=rows.map(({key,e,status,undone},i)=>{const selected=!undone&&activeSel?.has(key),firstIdx=!undone?earliestHistoryIndexForEditKey(key):-1,first=firstIdx>=0?state.versionHistory[firstIdx]:null,check=!undone?`<input class="change-log-select" type="checkbox" ${selected?'checked':''} aria-label="选择第 ${i+1} 项修改">`:'';const actions=(!undone&&!state.changeLogExport)?`<div class="change-log-row-actions"><button type="button" class="mini-btn soft-btn change-log-locate" data-edit-key="${escapeHtml(key)}">定位</button><button type="button" class="mini-btn soft-btn danger change-log-undo-one" data-edit-key="${escapeHtml(key)}">撤销此项</button><button type="button" class="mini-btn soft-btn change-log-before" data-edit-key="${escapeHtml(key)}">回到此项前</button></div>`:'';return `<article class="change-log-item v2322 ${status}${selected?' selected':''}" data-edit-key="${escapeHtml(key)}"><div class="change-log-index">${check}<span>${i+1}</span></div><div class="change-log-main"><strong>第 ${(e.page??0)+1} 页 · ${escapeHtml(editDisplayTitle(e))}<em class="change-status ${status}">${statusLabel(status)}</em></strong>${editDisplayDetail(e)}${first?`<small class="change-log-history-ref">首次记录：历史 #${first.id} · ${formatHistoryTime(first.time)}</small>`:''}</div>${actions}</article>`;}).join('');
  els.changeLogList.querySelectorAll('.change-log-select').forEach(cb=>cb.onchange=()=>{const key=cb.closest('[data-edit-key]')?.dataset.editKey;if(!key)return;const set=changeLogActiveSelection();if(cb.checked)set.add(key);else set.delete(key);renderChangeLog();});
  els.changeLogList.querySelectorAll('.change-log-locate').forEach(b=>b.onclick=()=>locateRevisionEdit(b.dataset.editKey));els.changeLogList.querySelectorAll('.change-log-undo-one').forEach(b=>b.onclick=()=>deleteRevisionEditByKey(b.dataset.editKey));els.changeLogList.querySelectorAll('.change-log-before').forEach(b=>b.onclick=()=>restoreBeforeRevisionEdit(b.dataset.editKey));syncChangeLogSelectionButtons();
};
openChangeLog=function(forExport=false){if(!state.id)return;state.changeLogExport=!!forExport;state.changeLogSelectedKeys.clear();state.changeLogFilter='all';if(forExport)state.exportSelectedKeys=new Set(state.edits.keys());els.changeLogFilters?.querySelectorAll('[data-change-filter]').forEach(b=>b.classList.toggle('active',b.dataset.changeFilter==='all'));renderChangeLog();els.changeLogConfirm.classList.toggle('hidden',!forExport);els.changeLogModal.classList.remove('hidden');};
if(els.changeLogFilters)els.changeLogFilters.querySelectorAll('[data-change-filter]').forEach(b=>b.onclick=()=>{state.changeLogFilter=b.dataset.changeFilter;els.changeLogFilters.querySelectorAll('[data-change-filter]').forEach(x=>x.classList.toggle('active',x===b));renderChangeLog();});
if(els.exportSelectAll)els.exportSelectAll.onclick=()=>setExportSelection([...state.edits.keys()]);if(els.exportSelectNone)els.exportSelectNone.onclick=()=>setExportSelection([]);if(els.exportSelectInvert)els.exportSelectInvert.onclick=()=>setExportSelection([...state.edits.keys()].filter(k=>!state.exportSelectedKeys.has(k)));if(els.exportSelectAnomaly)els.exportSelectAnomaly.onclick=()=>setExportSelection([...state.edits.entries()].filter(([k,e])=>editStatus(k,e)==='anomaly'||unresolvedPageNumberAnomaly(e.page)).map(([k])=>k));if(els.exportSelectCurrent)els.exportSelectCurrent.onclick=()=>setExportSelection([...state.edits.entries()].filter(([,e])=>e.page===state.currentPage).map(([k])=>k));

async function renderCurrentPage({jump=false}={}){if(!state.id)return;const page=state.currentPage;try{beginPageProgress(`正在高清渲染第 ${page+1} 页…`);await refreshPreview();state.pageRenderStatus.set(page,'success');state.resolvedAnomalyPages.add(page);renderPageNumberResults();renderChangeLog();toast(`第 ${page+1} 页已重新渲染，其他页面未处理`,3600);if(jump){const candidates=[...new Set((state.pageNumberScanResults||[]).map(r=>r.page).filter(p=>unresolvedPageNumberAnomaly(p)))].sort((a,b)=>a-b);const next=candidates.find(p=>p>page)??candidates[0];if(Number.isInteger(next)){closeChangeLog();await loadPage(next);toast(`已跳到下一异常页：第 ${next+1} 页`,3600);}else toast('当前没有未处理的异常页');}}catch(e){state.pageRenderStatus.set(page,'anomaly');renderChangeLog();toast(`本页渲染失败：${e.message}`,6200);}finally{endPageProgress();}}
if(els.renderCurrentPageBtn)els.renderCurrentPageBtn.onclick=()=>renderCurrentPage();if(els.renderNextAnomalyBtn)els.renderNextAnomalyBtn.onclick=()=>renderCurrentPage({jump:true});

async function validateEditsForWrite(edits){if(state.selected?.type==='text'){const draft=buildTextEdit(state.selected.item);if(!storedMatchesDraft(draft,state.selected.key))throw new Error('当前文字修订尚未运行，请先点击“开始运行”');}for(const edit of edits.filter(e=>e.type==='text')){const key=editKey('text',edit.page,edit.id);let f=state.feasibility.get(key),stale=!f||f.newText!==edit.newText||f.size!==edit.size||f.color!==edit.color||f.x!==edit.x||f.y!==edit.y||!visualAdjustEqual(f.visualAdjust,edit.visualAdjust)||!reusableGlyphEqual(f.reusableGlyph,edit.reusableGlyph);if(stale){f=await requestFeasibility(edit);state.feasibility.set(key,{...f,newText:edit.newText,size:edit.size,color:edit.color,x:edit.x,y:edit.y,visualAdjust:edit.visualAdjust,reusableGlyph:edit.reusableGlyph});}if(!editModeAllowed(f))throw new Error(`第 ${edit.page+1} 页 · ${f.reason||'该文字未通过修订检查'}`);}}
performExportPdf=async function(){if(!state.id)return;const selected=state.exportSelectedKeys instanceof Set?state.exportSelectedKeys:new Set(state.edits.keys()),edits=[...state.edits.entries()].filter(([k])=>selected.has(k)).map(([,e])=>e);if(!edits.length)return toast('本次导出没有选择任何修改');els.changeLogConfirm.disabled=true;els.exportBtn.disabled=true;els.exportBtn.textContent='生成中…';try{await validateEditsForWrite(edits);const r=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,edits})});if(!r.ok)throw new Error(await apiError(r));const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=state.outputName||'修订版.pdf';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);closeChangeLog();toast(`已导出 ${edits.length} 项选中修改：${a.download}`);}catch(e){toast(`导出失败：${e.message}`,6200);}finally{els.changeLogConfirm.disabled=false;els.exportBtn.disabled=false;els.exportBtn.textContent='导出';}};
if(els.changeLogConfirm)els.changeLogConfirm.onclick=performExportPdf;

function progressPayload(){return {schemaVersion:1,glyphLibrary:[...state.glyphLibrary.entries()],blockLibrary:[...state.blockLibrary.entries()],currentPage:state.currentPage,edits:[...state.edits.entries()],pageNumberTemplates:state.pageNumberTemplates,pageNumberPageOverrides:state.pageNumberPageOverrides,pageNumberManualTakeovers:[...ensurePageNumberTakeoverSet()],versionHistory:state.versionHistory,baselineId:state.currentBaselineId,previewQuality:state.previewQuality,changeLogTombstones:state.changeLogTombstones};}
async function saveProgress(){if(!state.id)return;const btn=els.saveProgressBtn;if(btn){btn.disabled=true;btn.textContent='保存中…';}try{const payload=progressPayload(),r=await fetch('/api/save-progress',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,state:payload})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();try{localStorage.setItem('pedit.oss.v1.lastProgress',JSON.stringify({id:state.id,name:state.name,savedAt:j.savedAt,state:payload}));}catch{}toast(`进度已保存 · ${String(j.savedAt||'').replace('T',' ')}`,4200);}catch(e){toast(`保存进度失败：${e.message}`,6200);}finally{if(btn){btn.disabled=false;btn.textContent='保存进度';}}}
async function saveAndContinue(){if(!state.id)return;const edits=allEdits();if(!edits.length)return toast('当前没有需要写入新基线的修改');const btn=els.saveContinueBtn,current=state.currentPage;if(btn){btn.disabled=true;btn.textContent='正在生成基线…';}beginPageProgress('正在保存并生成新的编辑基线…');try{await validateEditsForWrite(edits);const r=await fetch('/api/commit-baseline',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,edits,currentPage:current})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();state.currentBaselineId=Number(j.baselineId||0);state.baselineSeq=Math.max(state.baselineSeq||0,state.currentBaselineId);state.edits=new Map();state.feasibility=new Map();state.undo=[];state.redo=[];state.selected=null;state.pageNumberMatches=[];state.pageNumberScanResults=[];state.pageNumberPageOverrides={};state.pageNumberManualTakeovers=new Set();for(const slot of Object.keys(state.pageNumberTemplates||{}))state.pageNumberTemplates[slot]=null;renderPageNumberTemplateSlots();state.pageRenderStatus=new Map();state.resolvedAnomalyPages=new Set();state.changeLogSelectedKeys=new Set();state.exportSelectedKeys=new Set();state.changeLogTombstones=[];state.pageData=null;state.pageCount=Number(j.pageCount||state.pageCount);state.documentType=j.documentType||state.documentType;state.diagnosis=j.diagnosis||state.diagnosis;state.ocrAvailable=!!j.ocrAvailable;state.ocrReason=j.ocrReason||'';state.ocrLang=j.ocrLang||'';state.ocrBackend=j.ocrBackend||'';state.ocrBackendLabel=j.ocrBackendLabel||'';captureVersion(`基线 #${state.currentBaselineId}`,{page:current+1,detail:`已写入 ${j.appliedEdits||edits.length} 项修改`,baselineId:state.currentBaselineId},true);updateChangeCount();updateHistoryButtons();clearProps();buildThumbnails();await loadPage(Math.min(current,state.pageCount-1));toast(`已生成基线 #${state.currentBaselineId}，并以新 PDF 继续编辑`,5200);}catch(e){toast(`保存并编辑失败：${e.message}`,6500);}finally{endPageProgress();if(btn){btn.disabled=false;btn.textContent='保存并编辑';}}}
if(els.saveProgressBtn)els.saveProgressBtn.onclick=saveProgress;if(els.saveContinueBtn)els.saveContinueBtn.onclick=saveAndContinue;

restoreHistoryVersion=async function(){const v=versionById(state.historySelectedId);if(!v)return;const currentSnap=snapshot(),targetBaseline=Number(v.baselineId??0);if(currentSnap===v.snapshot&&targetBaseline===Number(state.currentBaselineId||0)){toast('当前已经是这个历史版本');return;}try{showLoading(true);if(targetBaseline!==Number(state.currentBaselineId||0)){const r=await fetch('/api/baseline/restore',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state.id,baselineId:targetBaseline})});if(!r.ok)throw new Error(await apiError(r));const j=await r.json();state.currentBaselineId=Number(j.baselineId||targetBaseline);state.documentType=j.documentType||state.documentType;state.diagnosis=j.diagnosis||state.diagnosis;state.ocrAvailable=!!j.ocrAvailable;state.ocrBackendLabel=j.ocrBackendLabel||state.ocrBackendLabel;buildThumbnails();}state.undo.push(currentSnap);if(state.undo.length>80)state.undo.shift();state.redo=[];state.changeLogTombstones=[];restoreSnapshot(v.snapshot);captureVersion(`返回到历史 #${v.id}`,{page:v.page,detail:v.name||v.label,sourceVersionId:v.id,baselineId:targetBaseline},true);closeVersionHistory();await loadPage(Math.max(0,(v.page||1)-1));toast(`已返回历史 #${v.id}${targetBaseline?` · 基线 #${targetBaseline}`:' · 原始基线'}`,4800);}catch(e){toast(`历史恢复失败：${e.message}`,6200);}finally{showLoading(false);}};
if(els.historyRestore)els.historyRestore.onclick=restoreHistoryVersion;

// v2.3.26: every persisted/generated edit exposes stable object metadata for deletion/history tooling.
function ensureEditObjectMetadata(e){if(!e||typeof e!=='object')return e;e.objectId=e.objectId||e.id||`obj-${e.page??0}-${Math.random().toString(36).slice(2,8)}`;e.batchId=e.batchId||e.pageNumberBatchId||`single-${e.objectId}`;e.role=e.role||e.pageNumberRole||(e.pageNumberSlot?`page-number-${e.pageNumberSlot}`:e.type||'edit');if(!e.bbox&&e.pdfBbox)e.bbox=[...e.pdfBbox];return e;}
allEdits=function(){return [...state.edits.values()].map(ensureEditObjectMetadata);};

async function resumeSavedProgress(){
  let saved=null;try{saved=JSON.parse(localStorage.getItem('pedit.oss.v1.lastProgress')||'null');}catch{}if(state.id)return;if(!saved?.id){toast('没有已保存的进度');return;}
  try{const r=await fetch(`/api/resume-progress?id=${encodeURIComponent(saved.id)}`);if(!r.ok){toast('已保存的会话不可用，请导入 PDF');return;}const j=await r.json(),p=j.progress||{},templates=p.pageNumberTemplates||{A:null,B:null};
    Object.assign(state,{id:j.id,name:j.name,outputName:j.outputName,pageCount:j.pageCount,currentPage:Math.max(0,Math.min((p.currentPage||0),j.pageCount-1)),pageData:null,edits:new Map(p.edits||[]),undo:[],redo:[],selected:null,zoom:1,viewMode:'fit-width',cleanPreview:false,feasibility:new Map(),selectionMode:'smart',cycleSig:'',cycleIndex:0,batchMatches:[],batchSource:null,runBusy:false,changeLogExport:false,glyphClipboard:null,glyphLibrary:new Map(p.glyphLibrary||[]),pendingReusableGlyph:null,blockClipboard:null,blockLibrary:new Map(p.blockLibrary||[]),pageNumberMatches:[],pageNumberScanResults:[],pageNumberTemplates:{A:null,B:null},pageNumberPageOverrides:p.pageNumberPageOverrides||{},pageNumberManualTakeovers:new Set(p.pageNumberManualTakeovers||[]),documentType:j.documentType||'unknown',diagnosis:j.diagnosis||null,ocrAvailable:!!j.ocrAvailable,ocrReason:j.ocrReason||'',ocrLang:j.ocrLang||'',ocrBackend:j.ocrBackend||'',ocrBackendLabel:j.ocrBackendLabel||'',versionHistory:p.versionHistory||[],versionSeq:Math.max(0,...(p.versionHistory||[]).map(x=>Number(x.id)||0)),historySelectedId:(p.versionHistory||[]).at(-1)?.id||null,pendingHistoryLabel:null,pendingHistoryMeta:null,changeLogSelectedKeys:new Set(),exportSelectedKeys:new Set(),changeLogTombstones:p.changeLogTombstones||[],changeLogFilter:'all',previewQuality:p.previewQuality||'auto',lastRenderScale:1.7,currentBaselineId:Number(j.baselineId||p.baselineId||0),baselineSeq:Number(j.baselineId||p.baselineId||0),pageRenderStatus:new Map(),resolvedAnomalyPages:new Set()});
    const extra=Math.max(0,Object.keys(templates).length-2);for(let i=0;i<extra;i++)addPageNumberSlot();for(const [slot,t] of Object.entries(templates))state.pageNumberTemplates[slot]=t;renderPageNumberTemplateSlots();if(els.previewQuality)els.previewQuality.value=state.previewQuality;els.selectionMode.value='smart';els.welcome.classList.add('hidden');els.viewer.classList.remove('hidden');els.pagesPanel.classList.remove('hidden');els.propertiesPanel.classList.remove('hidden');for(const b of [els.exportBtn,els.changeLogBtn,els.pageNumberBtn,els.historyBtn,els.saveProgressBtn,els.saveContinueBtn])if(b)b.disabled=false;els.fileNameLabel.textContent=j.name;if(els.topFileName)els.topFileName.textContent=j.name;els.pageCountBadge.textContent=j.pageCount;els.totalPagesLabel.textContent=j.pageCount;updateChangeCount();updateHistoryButtons();clearProps();buildThumbnails();updateEngineUi();await loadPage(state.currentPage);toast(`已恢复保存进度${j.savedAt?` · ${String(j.savedAt).replace('T',' ')}`:''}`,4800);
  }catch(e){console.warn('resume progress failed',e);}
}
// Restore only after an explicit user action; startup always stays empty.
const resumeProgressBtn = $('#resumeProgressBtn');
if(resumeProgressBtn)resumeProgressBtn.onclick=resumeSavedProgress;

// v2.3.29: one records entry, two existing feature panels.  The history and
// change-log engines deliberately remain separate so saved snapshots, baselines
// and per-edit operations keep their established behaviour.
Object.assign(els,{
  revisionRecordsBtn:$('#revisionRecordsBtn'),
  revisionTabChanges:$('#revisionTabChanges'), revisionTabHistory:$('#revisionTabHistory'),
  revisionChangesPanel:$('#revisionChangesPanel'), revisionHistoryPanel:$('#revisionHistoryPanel'),
  revisionRecordsSummary:$('#changeLogSummary')
});
els.changeLogBtn=els.revisionRecordsBtn;
els.historyModal=els.changeLogModal;

function setRevisionRecordsTab(tab='changes'){
  const history=tab==='history';
  els.revisionChangesPanel?.classList.toggle('hidden',history);
  els.revisionHistoryPanel?.classList.toggle('hidden',!history);
  els.revisionTabChanges?.classList.toggle('active',!history);
  els.revisionTabHistory?.classList.toggle('active',history);
  els.revisionTabChanges?.setAttribute('aria-selected',String(!history));
  els.revisionTabHistory?.setAttribute('aria-selected',String(history));
  if(history){renderVersionHistory(); if(els.revisionRecordsSummary)els.revisionRecordsSummary.textContent='选择任意历史节点可回退；Undo / Redo 保持可用。';}
  else if(els.revisionRecordsSummary)els.revisionRecordsSummary.textContent='查看、定位、撤销或导出本次修改。';
}
const V2329_OPEN_CHANGE_LOG=openChangeLog;
openChangeLog=function(forExport=false){V2329_OPEN_CHANGE_LOG(forExport);setRevisionRecordsTab('changes');};
openVersionHistory=function(){if(!state.id)return;V2329_OPEN_CHANGE_LOG(false);setRevisionRecordsTab('history');};
closeVersionHistory=function(){closeChangeLog();};
if(els.revisionRecordsBtn)els.revisionRecordsBtn.onclick=()=>openChangeLog(false);
if(els.revisionTabChanges)els.revisionTabChanges.onclick=()=>setRevisionRecordsTab('changes');
if(els.revisionTabHistory)els.revisionTabHistory.onclick=()=>setRevisionRecordsTab('history');
if(els.historyCancel)els.historyCancel.onclick=closeChangeLog;
if(els.historyRestore)els.historyRestore.onclick=restoreHistoryVersion;
if(els.changeLogClose)els.changeLogClose.onclick=closeChangeLog;
if(els.changeLogCancel)els.changeLogCancel.onclick=closeChangeLog;
