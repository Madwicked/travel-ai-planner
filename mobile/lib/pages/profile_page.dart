import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  String selectedCurrency = 'EUR';
  String selectedLanguage = 'System';

  final List<String> currencies = [
    'EUR',
    'USD',
    'GBP',
    'RSD',
    'CHF',
    'CAD',
    'AUD',
    'JPY',
    'CNY',
    'TRY',
    'AED',
    'THB',
  ];

  final List<String> languages = ['System', 'English', 'Русский'];

  @override
  void initState() {
    super.initState();
    loadSettings();
  }

  Future<void> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();

    final savedCurrency = prefs.getString('user_currency');
    final savedLanguage = prefs.getString('app_language');

    setState(() {
      selectedCurrency = savedCurrency ?? detectDefaultCurrency();

      selectedLanguage = savedLanguage ?? detectDefaultLanguage();
    });
  }

  String detectDefaultCurrency() {
    final locale = WidgetsBinding.instance.platformDispatcher.locale;

    switch (locale.countryCode) {
      case 'RS':
        return 'RSD';
      case 'US':
        return 'USD';
      case 'GB':
        return 'GBP';
      case 'CH':
        return 'CHF';
      case 'CA':
        return 'CAD';
      case 'AU':
        return 'AUD';
      case 'JP':
        return 'JPY';
      case 'CN':
        return 'CNY';
      case 'TR':
        return 'TRY';
      case 'AE':
        return 'AED';
      case 'TH':
        return 'THB';
      default:
        return 'EUR';
    }
  }

  String detectDefaultLanguage() {
    final languageCode =
        WidgetsBinding.instance.platformDispatcher.locale.languageCode;

    switch (languageCode) {
      case 'ru':
        return 'Русский';
      case 'en':
        return 'English';
      default:
        return 'System';
    }
  }

  Future<void> saveCurrency(String currency) async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('user_currency', currency);

    final trips = await ApiService.getTrips();

    for (final trip in trips) {
      final tripId = trip['id'];

      await ApiService.updateUserCurrency(
        tripId: tripId,
        userCurrency: currency,
      );
    }

    if (!mounted) {
      return;
    }

    setState(() {
      selectedCurrency = currency;
    });
  }

  Future<void> saveLanguage(String language) async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('app_language', language);

    setState(() {
      selectedLanguage = language;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Currency',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: selectedCurrency,
            decoration: const InputDecoration(border: OutlineInputBorder()),
            items: currencies.map((currency) {
              return DropdownMenuItem(value: currency, child: Text(currency));
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                saveCurrency(value);
              }
            },
          ),
          const SizedBox(height: 24),
          const Text(
            'Language',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: selectedLanguage,
            decoration: const InputDecoration(border: OutlineInputBorder()),
            items: languages.map((language) {
              return DropdownMenuItem(value: language, child: Text(language));
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                saveLanguage(value);
              }
            },
          ),
        ],
      ),
    );
  }
}
