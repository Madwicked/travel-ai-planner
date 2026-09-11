import 'package:flutter/widgets.dart';

class AppLocalizations {
  const AppLocalizations(this.locale);

  final Locale locale;

  static const supportedLocales = [Locale('en'), Locale('ru')];

  static AppLocalizations of(BuildContext context) =>
      Localizations.of<AppLocalizations>(context, AppLocalizations) ??
      const AppLocalizations(Locale('en'));

  String text(String value) =>
      _translations[locale.languageCode]?[value] ?? value;

  static const _translations = <String, Map<String, String>>{
    'ru': {
      'Travel AI Planner': 'Планировщик путешествий AI',
      'No trips yet': 'Поездок пока нет',
      'My Trips': 'Мои поездки',
      'Create trip': 'Создать поездку',
      'Delete trip': 'Удалить поездку',
      'Delete trip?': 'Удалить поездку?',
      'This trip and all its saved data will be deleted.':
          'Эта поездка и все сохранённые данные будут удалены.',
      'Cancel': 'Отмена',
      'Delete': 'Удалить',
      'Trip deleted.': 'Поездка удалена.',
      'Create Trip': 'Создать поездку',
      'Plan your perfect trip ✈️': 'Спланируйте идеальное путешествие ✈️',
      'Tell us about your trip and AI will create a personalized itinerary.':
          'Расскажите о поездке, и AI создаст персональный маршрут.',
      'From': 'Откуда',
      'To': 'Куда',
      'Travel dates': 'Даты поездки',
      'Select date': 'Выберите дату',
      'Travelers': 'Путешественники',
      'traveler': 'путешественник',
      'travelers': 'путешественников',
      'Generating...': 'Создание...',
      'Generate My Trip': 'Создать маршрут',
      'Please select cities from the suggestions and fill in all fields.':
          'Выберите города из подсказок и заполните все поля.',
      'End date must be after the start date.':
          'Дата окончания должна быть позже даты начала.',
      'Hotel Options': 'Варианты отелей',
      'Transport Options': 'Варианты транспорта',
      'Return Transport': 'Обратный транспорт',
      'Places to Visit': 'Места для посещения',
      'Trip Details': 'Детали поездки',
      'Currency': 'Валюта',
      'Select currency': 'Выберите валюту',
      'Outbound Transport': 'Транспорт туда',
      'Choose outbound transport': 'Выбрать транспорт туда',
      'Choose return transport': 'Выбрать транспорт обратно',
      'Hotel': 'Отель',
      'Choose hotel': 'Выбрать отель',
      'Places': 'Места',
      'Choose places': 'Выбрать места',
      'Change places': 'Изменить места',
      'Change': 'Изменить',
      'View itinerary': 'Открыть маршрут',
      'AI Itinerary': 'Маршрут AI',
      'Your personalized trip itinerary': 'Ваш персональный маршрут поездки',
      'Morning': 'Утро',
      'Lunch': 'День',
      'Afternoon': 'После полудня',
      'Evening': 'Вечер',
    },
  };
}

class AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => AppLocalizations.supportedLocales.any(
    (item) => item.languageCode == locale.languageCode,
  );

  @override
  Future<AppLocalizations> load(Locale locale) async =>
      AppLocalizations(locale);

  @override
  bool shouldReload(AppLocalizationsDelegate old) => false;
}

extension AppLocalizationsBuildContext on BuildContext {
  String tr(String value) => AppLocalizations.of(this).text(value);
}
