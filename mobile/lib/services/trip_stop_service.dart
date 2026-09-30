import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import '../models/trip_stop.dart';

class TripStopService {
  static Future<List<TripStop>> getTripStops(int tripId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/stops');

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['stops'] as List)
        .map((stop) => TripStop.fromJson(Map<String, dynamic>.from(stop)))
        .toList();
  }

  static Future<TripStop> createTripStop({
    required int tripId,
    required String city,
    String? country,
    double? latitude,
    double? longitude,
    required DateTime startDate,
    required DateTime endDate,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/stops');

    final body = {
      'city': city,
      'country': country,
      'latitude': latitude,
      'longitude': longitude,
      'start_date': startDate.toIso8601String().split('T').first,
      'end_date': endDate.toIso8601String().split('T').first,
    };

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return TripStop.fromJson(Map<String, dynamic>.from(data['stop']));
  }

  static Future<Map<String, dynamic>> updateTripStop({
    required int tripId,
    required int stopId,
    required String city,
    String? country,
    double? latitude,
    double? longitude,
    required DateTime startDate,
    required DateTime endDate,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/'
      '$tripId/stops/$stopId',
    );

    final body = {
      'city': city,
      'country': country,
      'latitude': latitude,
      'longitude': longitude,
      'start_date': startDate.toIso8601String().split('T').first,
      'end_date': endDate.toIso8601String().split('T').first,
    };

    final response = await http.put(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return Map<String, dynamic>.from(data);
  }

  static Future<void> deleteTripStop({
    required int tripId,
    required int stopId,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/stops/$stopId',
    );

    final response = await http.delete(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<List<Map<String, dynamic>>> getConsistencyWarnings(
    int tripId,
  ) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/consistency-warnings',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    final warnings = data['warnings'];

    if (warnings is! List) {
      return [];
    }

    return warnings
        .whereType<Map>()
        .map((warning) => Map<String, dynamic>.from(warning))
        .toList();
  }
}
