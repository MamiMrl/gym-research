from telegram import InlineKeyboardButton, InlineKeyboardMarkup

STATUS_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✓ As planned", callback_data="status:as_planned"),
        InlineKeyboardButton("↑ Too easy",   callback_data="status:too_easy"),
    ],
    [
        InlineKeyboardButton("↓ Struggled",  callback_data="status:struggled"),
        InlineKeyboardButton("✗ Skipped",    callback_data="status:skipped"),
    ],
])

SKIP_NOTE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Skip note", callback_data="skip_note")]
])

SUBMIT_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Submit and generate plan", callback_data="submit")]
])
