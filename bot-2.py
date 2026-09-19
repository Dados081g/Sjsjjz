import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

# ───────────────────────── НАСТРОЙКИ ─────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")

# Цвета кнопок: danger = красная, success = зелёная, primary = синяя
RED, GREEN, BLUE = "danger", "success", "primary"


def em(emoji_id: str, fallback: str) -> str:
    """Премиум-эмодзи в тексте сообщения."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


# ───────────────────────── ТЕКСТЫ ─────────────────────────
LINE = "➖➖➖➖➖➖➖➖➖➖➖➖"

WELCOME_TEXT = (
    f"{em('5280475364865381482', '💎')} Добро пожаловать!\n\n"
    "Вы попали в магазин игровых утилит. Здесь можно пополнить баланс "
    "и купить нужный товар в пару нажатий.\n\n"
    f"{em('5258024802010026053', '🛒')} Каталог — весь ассортимент\n"
    f"{em('5886285355279193209', '👛')} Профиль — баланс, заказы, промокоды\n"
    f"{em('5983580310292402968', '🎙')} Поддержка — если что-то пошло не так\n\n"
    f"{em('5766994197705921104', '☝️')} Перед покупкой ознакомьтесь с правилами "
    "и политикой конфиденциальности — они в разделе «Профиль»."
)

CATALOG_TEXT = (
    f"{em('5258024802010026053', '🛒')} Выберите вашу игру\n\n"
    f"{em('5280475364865381482', '☝️')} Все разделы магазина — на кнопках ниже."
)

DEVICES_TEXT = (
    f"{em('5258508428212445001', '🎮')} OXIDE\n"
    f"{LINE}\n"
    f"{em('5258514780469075716', '📥')} Выберите ваше устройство:"
)

TARIFFS_TEXT = (
    f"{em('5942734685976138521', '🖥')} OXIDE · Android • NROOT\n"
    f"{LINE}\n"
    f"{em('5280640845660330048', '🔎')} Ознакомьтесь с тарифами — "
    "у каждого свой функционал и срок."
)

CARD_TEXT = (
    "OXIDE ANDROID\n"
    f"{LINE}\n"
    f"{em('5775896410780079073', '🕓')} Срок: 1 день\n"
    f"{em('5231449120635370684', '💸')} Цена: 160 ₽"
)

PROFILE_TEXT = (
    f"{em('5886285355279193209', '👛')} Профиль\n\n"
    "ID: {user_id}\n"
    "Баланс: 0 ₽\n"
    "Заказов: 0\n\n"
    "Здесь же будут промокоды, правила и политика конфиденциальности."
)


# ───────────────────────── КЛАВИАТУРЫ ─────────────────────────
def ib(text: str, data: str, emoji: str | None = None, style: str | None = None):
    return InlineKeyboardButton(
        text=text,
        callback_data=data,
        icon_custom_emoji_id=emoji,
        style=style,
    )


def kb(*buttons) -> InlineKeyboardMarkup:
    """Кнопки друг под другом, на всю ширину (как на скриншоте)."""
    return InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])


# Главное меню — прямо под сообщением бота
MAIN_KB = kb(
    ib("Каталог", "go:catalog", emoji="5229064374403998351", style=RED),
    ib("Мой профиль", "go:profile", emoji="5904630315946611415", style=BLUE),
)

CATALOG_KB = kb(
    ib("Oxide", "go:devices", style=RED),
    ib("Главное меню", "go:main"),
)

PROFILE_KB = kb(ib("Главное меню", "go:main"))

DEVICES_KB = kb(
    ib("Android Non Root", "go:tariffs", emoji="5258514780469075716", style=RED),
    ib("Назад", "go:catalog"),
)

TARIFFS_KB = kb(
    ib("Cry4me 1D 160 руб", "go:card", emoji="5399986364634641475", style=RED),
    ib("Назад", "go:devices"),
)

CARD_KB = kb(
    ib("Купить за 160Р", "go:pay", emoji="5258024802010026053", style=GREEN),
    ib("Назад", "go:tariffs"),
)

PAY_KB = kb(
    ib("Оплатить по СБП", "pay:sbp", emoji="5280973778640211229", style=GREEN),
    ib("Назад", "go:card"),
)

# экран → (текст, клавиатура)
SCREENS = {
    "main": (WELCOME_TEXT, MAIN_KB),
    "catalog": (CATALOG_TEXT, CATALOG_KB),
    "profile": (PROFILE_TEXT, PROFILE_KB),
    "devices": (DEVICES_TEXT, DEVICES_KB),
    "tariffs": (TARIFFS_TEXT, TARIFFS_KB),
    "card": (CARD_TEXT, CARD_KB),
    "pay": (CARD_TEXT, PAY_KB),
}

# ───────────────────────── ЛОГИКА ─────────────────────────
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    # Убираем старую клавиатуру внизу экрана (если осталась от прошлой версии)
    tmp = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await tmp.delete()

    text, markup = SCREENS["main"]
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("go:"))
async def navigate(cb: CallbackQuery):
    screen = cb.data.split(":", 1)[1]
    text, markup = SCREENS[screen]
    text = text.replace("{user_id}", str(cb.from_user.id))
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await cb.answer()


@router.callback_query(F.data == "pay:sbp")
async def pay_sbp(cb: CallbackQuery):
    # TODO: здесь создать платёж по СБП в вашей платёжной системе
    # и отправить пользователю ссылку/QR.
    await cb.answer("Оплата по СБП пока не подключена.", show_alert=True)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
