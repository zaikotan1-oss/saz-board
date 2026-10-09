/**
 * 感度くらべ の記録置き場（Google Apps Script のウェブアプリ）
 * スプレッドシートの「runs」シートに 1 行 1 記録で貯める。
 *  GET  ?action=list            → 全記録を JSON で返す
 *  POST (text/plain の JSON)     → {action:"add", row:{...}} / {action:"delete", id, token}
 * 行: id, ts, name, drill, sens, saz, score, token
 * token は端末ごとの合言葉。自分の記録だけ消せるようにするための物（秘密ではない）。
 */
var SHEET_ID = '1AmoGi0G_mCDFM9lszXgKgK9y4iFV0JKX1D7w63y5Umo'; // 記録を貯めるスプレッドシート
var SHEET = 'runs';
var HEAD = ['id', 'ts', 'name', 'drill', 'sens', 'saz', 'score', 'token'];

function sheet_() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sh = ss.getSheetByName(SHEET);
  if (!sh) { sh = ss.insertSheet(SHEET); sh.appendRow(HEAD); }
  return sh;
}
function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
function rows_() {
  var sh = sheet_();
  var v = sh.getDataRange().getValues();
  var res = [];
  for (var i = 1; i < v.length; i++) {
    if (!v[i][0]) continue;
    res.push({ id: String(v[i][0]), ts: Number(v[i][1]), name: String(v[i][2]), drill: String(v[i][3]),
               sens: Number(v[i][4]), saz: Number(v[i][5]), score: Number(v[i][6]), token: String(v[i][7] || '') });
  }
  return res;
}
function strip_(r) { return { id: r.id, ts: r.ts, name: r.name, drill: r.drill, sens: r.sens, saz: r.saz, score: r.score, tk: r.token ? r.token.slice(0, 4) : '' }; }

function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || 'list';
  if (action === 'list') return out_({ ok: true, rows: rows_().map(strip_) });
  return out_({ ok: false, error: 'unknown action' });
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var sh = sheet_();
    if (body.action === 'add') {
      var r = body.row || {};
      var name = String(r.name || '').trim().slice(0, 20);
      var drill = String(r.drill || 'Hexakill').slice(0, 40);
      var sens = Number(r.sens), saz = Number(r.saz), score = Number(r.score);
      var token = String(r.token || '').slice(0, 32);
      if (!name || !isFinite(sens) || !isFinite(score) || score < 0 || score > 100000) return out_({ ok: false, error: 'bad row' });
      var id = Utilities.getUuid().slice(0, 8);
      var ts = Date.now();
      sh.appendRow([id, ts, name, drill, sens, isFinite(saz) ? saz : '', score, token]);
      return out_({ ok: true, id: id, ts: ts });
    }
    if (body.action === 'delete') {
      var v = sh.getDataRange().getValues();
      for (var i = 1; i < v.length; i++) {
        if (String(v[i][0]) === String(body.id)) {
          if (String(v[i][7] || '') !== String(body.token || '')) return out_({ ok: false, error: 'not yours' });
          sh.deleteRow(i + 1);
          return out_({ ok: true });
        }
      }
      return out_({ ok: false, error: 'not found' });
    }
    return out_({ ok: false, error: 'unknown action' });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}
