import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api_config.dart';

class ApiService {
  static Future<Map<String, dynamic>> createTrip({
    required String origin,
    required String originCountry,
    required double originLatitude,
    required double originLongitude,

    required String destination,
    required String destinationCountry,

    required String destinationCountryCode,
    required double destinationLatitude,
    required double destinationLongitude,

    required String startDate,
    required String endDate,
    required int travelers,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips');

    final body = {
      'origin': origin,
      'origin_country': originCountry,
      'origin_latitude': originLatitude,
      'origin_longitude': originLongitude,

      'destination': destination,
      'destination_country': destinationCountry,
      'destination_country_code': destinationCountryCode,
      'destination_latitude': destinationLatitude,
      'destination_longitude': destinationLongitude,

      'start_date': startDate,
      'end_date': endDate,
      'travelers': travelers,
    };

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    return jsonDecode(response.body);
  }

  static Future<List<dynamic>> getTrips() async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips');

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return data['trips'] ?? [];
  }

  static Future<void> updateUserCurrency({
    required int tripId,
    required String userCurrency,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/currency');

    final response = await http.put(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'user_currency': userCurrency}),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<void> updateFoodPreference({
    required int tripId,
    required String foodPreference,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/food');

    final response = await http.put(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'food_preference': foodPreference}),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<void> updateTripDates({
    required int tripId,
    required String startDate,
    required String endDate,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/dates');

    final response = await http.put(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'start_date': startDate, 'end_date': endDate}),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> getBudget({required int tripId}) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/budget');

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    return jsonDecode(response.body);
  }

  static Future<List<dynamic>> searchCities(String query) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/locations/search')
        .replace(queryParameters: {'q': query});

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return data['cities'] ?? [];
  }

  static Future<void> deleteTrip(int tripId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId');

    final response = await http.delete(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }
}
