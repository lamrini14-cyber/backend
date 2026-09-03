/**
 * SUNU YARAMA — Google Apps Script for Order Webhook
 * 
 * HOW TO SET UP:
 * 1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1cknxTGLDqtIlQFSiu1goGNeqU3N-P2aXZnAHZXOHs40/edit
 * 2. Go to Extensions > Apps Script
 * 3. Delete any existing code and paste this entire script
 * 4. Click Deploy > New deployment
 * 5. Select type: Web app
 * 6. Set "Execute as": Me
 * 7. Set "Who has access": Anyone
 * 8. Click Deploy and copy the URL
 * 9. Add the URL to your backend env: GOOGLE_SHEETS_WEBHOOK_URL=<paste URL here>
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);

    var row = [
      data.date || "",
      data.order_id || "",
      data.country || "Sénégal",
      data.name || "",
      data.phone || "",
      data.product || "",
      data.sku || "",
      data.quantity || "",
      data.total_price || "",
      data.currency || "CFA",
      data.status || ""
    ];

    sheet.appendRow(row);

    return ContentService
      .createTextOutput(JSON.stringify({ result: "success" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ result: "error", message: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({ status: "ok", message: "SUNU YARAMA webhook is active" }))
    .setMimeType(ContentService.MimeType.JSON);
}
