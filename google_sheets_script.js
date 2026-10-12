/**
 * ============================================================================
 * GOOGLE APPS SCRIPT KODI (PRO EDITION - 100% XAVFSIZ VA ANIQ)
 * ============================================================================
 * 
 * JADVALINGIZDAGI 10 TA USTUNNING ANIQ TARTIBI:
 * A (1): Telegram ID       (Masalan: 7878401108)
 * B (2): Username          (Masalan: @Send_store_uz)
 * C (3): TG Profil Ismi    (Masalan: Abdurauf)
 * D (4): Ism               (Masalan: Abdurauf)
 * E (5): Familiya          (Masalan: Nasrullayev)
 * F (6): Telefon           (Masalan: +998901234567)
 * G (7): Tug'ilgan Yili    (Masalan: 2005)
 * H (8): Yakunlangan       (Masalan: Ha ✅ yoki Yo'q ⏳)
 * I (9): Yaratilgan Vaqt   (Masalan: 2026-10-13 00:10:00 - SAQLANIB QOLADI)
 * J (10): Yangilangan Vaqt (Masalan: 2026-10-13 00:15:30 - HAR SAFAR YANGILANADI)
 * ============================================================================
 */

// Sizning Google Sheets jadvalingiz ID si (brauzer havolasidan olingan)
var SPREADSHEET_ID = "14mp_slEQMB7UBZax-ysudBwPWxcS5MaZksR-0SqUbI8";

/**
 * Jadvalni har qanday holatda (bog'langan yoki alohida loyiha bo'lsa ham) topuvchi funksiya
 */
function getTargetSheet() {
  var ss = null;
  try {
    ss = SpreadsheetApp.getActiveSpreadsheet();
  } catch (e) {}
  if (!ss) {
    try {
      ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    } catch (e) {}
  }
  if (!ss) {
    throw new Error("Jadval topilmadi! SPREADSHEET_ID ni tekshiring: " + SPREADSHEET_ID);
  }
  return ss.getSheetByName("Sheet1") || ss.getActiveSheet() || ss.getSheets()[0];
}

/**
 * ID ni faqat toza raqamlarga aylantirish (har qanday formatda aniq topadi)
 */
function cleanId(val) {
  if (val === null || val === undefined) return "";
  return String(val).replace(/[^0-9]/g, "").trim();
}

/**
 * Toshkent vaqti formati
 */
function formatTashkentTime(dateObj) {
  var d = dateObj || new Date();
  return Utilities.formatDate(d, "Asia/Tashkent", "yyyy-MM-dd HH:mm:ss");
}

/**
 * 1. WEBHOOK ORQALI MA'LUMOT QABUL QILISH VA YANGILASH (doPost)
 */
function doPost(e) {
  // Parallel so'rovlarni tartibga solish uchun LockService (navbat tizimi)
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // 30 soniya kutadi
  } catch (lockErr) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: "Server band (lock timeout)"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var sheet = getTargetSheet();
    var contents = (e && e.postData && e.postData.contents) ? e.postData.contents : "{}";
    var data = JSON.parse(contents);

    var targetId = cleanId(data.user_id);
    if (!targetId) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "user_id topilmadi"
      })).setMimeType(ContentService.MimeType.JSON);
    }

    var nowTashkent = formatTashkentTime(new Date());
    var isCompletedText = (data.is_completed === true || data.is_completed === "true") ? "Ha ✅" : "Yo'q ⏳";
    var usernameFormatted = data.username ? ("@" + String(data.username).replace(/^@/, "")) : "";
    var phoneStr = data.phone ? String(data.phone).trim() : "";

    var lastRow = sheet.getLastRow();
    var firstMatchRow = -1;
    var duplicateRows = [];
    var preservedCreatedAt = "";

    // Mavjud foydalanuvchini jadvaldan qidiramiz
    if (lastRow > 1) {
      var allData = sheet.getRange(2, 1, lastRow - 1, Math.max(sheet.getLastColumn(), 10)).getValues();

      for (var i = 0; i < allData.length; i++) {
        var currentRowNum = i + 2;
        var row = allData[i];

        // 1-ustun (A ustun) Telegram ID ni tekshiramiz
        var colAId = cleanId(row[0]);
        var isMatch = (colAId !== "" && colAId === targetId);

        // Agar A ustunda topilmasa (eski xato qatorlar uchun 2..5 ustunlarni ham ko'ramiz)
        if (!isMatch) {
          for (var c = 1; c < Math.min(row.length, 5); c++) {
            if (cleanId(row[c]) === targetId) {
              isMatch = true;
              break;
            }
          }
        }

        if (isMatch) {
          if (firstMatchRow === -1) {
            firstMatchRow = currentRowNum;
            // 9-ustun (I ustun) dagi Yaratilgan Vaqtni asrab qolamiz
            var existingCreated = row[8];
            if (existingCreated) {
              if (existingCreated instanceof Date) {
                preservedCreatedAt = formatTashkentTime(existingCreated);
              } else {
                preservedCreatedAt = String(existingCreated).trim();
              }
            }
          } else {
            // Dublikat qatorlarni o'chirish uchun belgilaymiz
            duplicateRows.push(currentRowNum);
          }
        }
      }
    }

    var finalCreatedAt = preservedCreatedAt || data.created_at || nowTashkent;
    var finalUpdatedAt = data.updated_at || nowTashkent;

    // 10 ta ustunning qat'iy tartibi:
    var rowData = [
      targetId,                                     // A (1): Telegram ID
      usernameFormatted,                            // B (2): Username
      String(data.tg_first_name || ""),             // C (3): TG Profil Ismi
      String(data.first_name || ""),                // D (4): Ism
      String(data.last_name || ""),                 // E (5): Familiya
      phoneStr,                                     // F (6): Telefon
      data.birth_year ? String(data.birth_year) : "", // G (7): Tug'ilgan Yili
      isCompletedText,                              // H (8): Yakunlangan
      finalCreatedAt,                               // I (9): Yaratilgan Vaqt (Asrab qolinadi)
      finalUpdatedAt                                // J (10): Yangilangan Vaqt (Har doim yangilanadi)
    ];

    if (firstMatchRow !== -1) {
      // Mavjud qatorni formatini matn (plain text) qilib yangilaymiz:
      sheet.getRange(firstMatchRow, 1).setNumberFormat("@");
      sheet.getRange(firstMatchRow, 6).setNumberFormat("@");
      sheet.getRange(firstMatchRow, 1, 1, 10).setValues([rowData]);

      // Ortiqcha dublikat qatorlarni pastdan tepaga qarab o'chiramiz:
      for (var d = duplicateRows.length - 1; d >= 0; d--) {
        sheet.deleteRow(duplicateRows[d]);
      }
    } else {
      // Yangi foydalanuvchi bo'lsa:
      var newRowNum = lastRow + 1;
      sheet.getRange(newRowNum, 1).setNumberFormat("@");
      sheet.getRange(newRowNum, 6).setNumberFormat("@");
      sheet.getRange(newRowNum, 1, 1, 10).setValues([rowData]);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      action: firstMatchRow !== -1 ? "updated" : "inserted",
      row: firstMatchRow !== -1 ? firstMatchRow : (lastRow + 1),
      duplicatesRemoved: duplicateRows.length,
      user_id: targetId,
      createdAt: finalCreatedAt,
      updatedAt: finalUpdatedAt
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

/**
 * 2. BRAUZERDA TEKSHIRISH (doGet)
 */
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "ok",
    version: "3.2-PRO",
    message: "Google Sheets Webhook 3.2 muvaffaqiyatli ishlamoqda!",
    columns: 10,
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * 3. JADVALDAGI ESKI BUZILGAN QATORLARNI DARHOL TOZALASH (RUN BOSISH UCHUN)
 */
function tozalashVaTartiblash() {
  var sheet = getTargetSheet();
  var lastRow = sheet.getLastRow();

  // Sarlavhalarni 10 ta ustun bilan tekislash
  var headers = [
    "Telegram ID",
    "Username",
    "TG Profil Ismi",
    "Ism",
    "Familiya",
    "Telefon",
    "Tug'ilgan Yili",
    "Yakunlangan",
    "Yaratilgan Vaqt",
    "Yangilangan Vaqt"
  ];
  sheet.getRange(1, 1, 1, 10).setValues([headers]);

  if (lastRow <= 1) {
    Logger.log("Jadvalda ma'lumotlar yo'q.");
    return;
  }

  var values = sheet.getRange(2, 1, lastRow - 1, Math.max(sheet.getLastColumn(), 10)).getValues();
  var seenUsers = {};
  var rowsToDelete = [];

  for (var i = 0; i < values.length; i++) {
    var rowNum = i + 2;
    var row = values[i];

    var colAStr = String(row[0] || "");
    var colBStr = String(row[1] || "");

    var uid = "";
    var isShiftedRow = false;

    // Agar 1-ustunda sana turgan bo'lsa (eski xato)
    if (colAStr.match(/^\d{4}-\d{2}-\d{2}/) && cleanId(colBStr) !== "") {
      uid = cleanId(colBStr);
      isShiftedRow = true;
    } else {
      uid = cleanId(colAStr);
    }

    if (!uid) continue;

    if (!seenUsers[uid]) {
      seenUsers[uid] = rowNum;

      var cleanRow = [];
      if (isShiftedRow) {
        cleanRow = [
          uid,
          row[2] || "",
          "",
          row[3] || "",
          row[4] || "",
          row[5] || "",
          row[6] || "",
          "Ha ✅",
          row[0] || formatTashkentTime(),
          row[0] || formatTashkentTime()
        ];
      } else {
        cleanRow = [
          uid,
          row[1] || "",
          row[2] || "",
          row[3] || "",
          row[4] || "",
          row[5] || "",
          row[6] || "",
          row[7] || "Ha ✅",
          row[8] || formatTashkentTime(),
          row[9] || formatTashkentTime()
        ];
      }
      sheet.getRange(rowNum, 1).setNumberFormat("@");
      sheet.getRange(rowNum, 6).setNumberFormat("@");
      sheet.getRange(rowNum, 1, 1, 10).setValues([cleanRow]);
    } else {
      rowsToDelete.push(rowNum);
    }
  }

  for (var d = rowsToDelete.length - 1; d >= 0; d--) {
    sheet.deleteRow(rowsToDelete[d]);
  }

  Logger.log("Tozalash yakunlandi! O'chirilgan dublikatlar: " + rowsToDelete.length);
}

/**
 * 4. TO'G'RIDAN-TO'G'RI TEST QILISH (APPS SCRIPTDA RUN BOSISH UCHUN)
 */
function testYozish() {
  var testData = {
    postData: {
      contents: JSON.stringify({
        user_id: "7878401108",
        username: "Send_store_uz",
        tg_first_name: "Abdurauf",
        first_name: "Abdurauf",
        last_name: "Nasrullayev",
        phone: "+998901234567",
        birth_year: "2007",
        is_completed: true,
        created_at: "2026-10-13 00:10:00",
        updated_at: formatTashkentTime()
      })
    }
  };

  var res = doPost(testData);
  Logger.log("Natija: " + res.getContent());
}
