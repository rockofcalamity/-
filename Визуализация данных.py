import io
import telebot
from telebot import types
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image

matplotlib.use('Agg')

API_TOKEN = '7634387775:AAGvG_-Wtd3-8qmnRBDnYhy2gkbF_Vrr9Rc'
bot = telebot.TeleBot(API_TOKEN)

user_data = {}


@bot.message_handler(commands=['generate'])
def generate(message):
    bot.send_message(message.chat.id,
                     "Введите данные для графика в формате 'x1,y1 x2,y2 x3,y3 ...' (например, '1,10 2,15 3,13 4,17').")


@bot.message_handler(func=lambda message: True)
def data(message):
    data_input = message.text
    user_data[message.from_user.id] = {'data': data_input.split(), 'xlabel': None, 'ylabel': None}
    bot.send_message(message.chat.id, "Данные получены. Теперь введите подпись для оси X:")
    bot.register_next_step_handler(message, x)


def x(message):
    user_data[message.from_user.id]['xlabel'] = message.text
    bot.send_message(message.chat.id, "Теперь введите подпись для оси Y:")
    bot.register_next_step_handler(message, y)


def y(message):
    user_data[message.from_user.id]['ylabel'] = message.text
    bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы выбрать тип графика:", reply_markup=inline_keyboard())


def inline_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Столбчатый график", callback_data='bar'))
    keyboard.add(types.InlineKeyboardButton("Линейный график", callback_data='line'))
    keyboard.add(types.InlineKeyboardButton("Точечный график", callback_data='scatter'))
    keyboard.add(types.InlineKeyboardButton("Гистограмма", callback_data='histogram'))
    keyboard.add(types.InlineKeyboardButton("Круговая диаграмма", callback_data='pie'))
    keyboard.add(types.InlineKeyboardButton("График с областями", callback_data='area'))
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def button(call):
    plot_type = call.data
    user_info = user_data.get(call.from_user.id)
    if not user_info or not user_info['data']:
        bot.send_message(call.message.chat.id, "Сначала введите данные для графика с помощью команды /start.")
        return
    data_points = user_info['data']
    x = []
    y = []
    for point in data_points:
        try:
            xi, yi = map(float, point.split(','))
            x.append(xi)
            y.append(yi)
        except ValueError:
            bot.send_message(call.message.chat.id,
                             f"Ошибка в данных: '{point}'. Убедитесь, что они введены в правильном формате.")
            return
    xlabel = user_info['xlabel']
    ylabel = user_info['ylabel']
    fig = create_plot(plot_type, x, y, xlabel, ylabel)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = Image.open(buf)
    if buf.getbuffer().nbytes == 0:
        bot.send_message(call.message.chat.id, "Ошибка: изображение пустое.")
        return

    bot.send_photo(call.message.chat.id, photo=buf.getvalue())
    buf.close()
    plt.close(fig)


def create_plot(plot_type, x, y, xlabel, ylabel):
    plt.figure(figsize=(8, 6))
    if plot_type == 'bar':
        plt.bar(x, y, color='skyblue')
        plt.title('Столбчатый график', fontsize=14)
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
    elif plot_type == 'line':
        plt.plot(x, y, marker='o', linestyle='-', color='orange')
        plt.title('Линейный график', fontsize=14)
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True)
    elif plot_type == 'scatter':
        plt.scatter(x, y, color='green')
        plt.title('Точечный график', fontsize=14)
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True)
    elif plot_type == 'histogram':
        plt.hist(y, bins=10, color='purple', alpha=0.7)
        plt.title('Гистограмма', fontsize=14)
        plt.xlabel('Значения', fontsize=12)
        plt.ylabel('Частота', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
    elif plot_type == 'pie':
        plt.pie(y, labels=x, autopct='%1.1f%%', startangle=140)
        plt.title('Круговая диаграмма', fontsize=14)
    elif plot_type == 'area':
        plt.fill_between(x, y, color='lightblue', alpha=0.5)
        plt.title('График с областями', fontsize=14)
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True)

    return plt.gcf()

bot.polling()
