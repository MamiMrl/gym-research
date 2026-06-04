from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CONFIRM_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✓ Confirm & email", callback_data="confirm"),
        InlineKeyboardButton("↻ Re-record",       callback_data="rerecord"),
    ],
])
