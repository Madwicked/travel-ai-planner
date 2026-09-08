import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import '../models/place.dart';

class PlaceService {
  static Future<List<Place>> getPlaceOptions(int tripId) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/places/options',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['options'] as List)
        .map((place) => Place.fromJson(Map<String, dynamic>.from(place)))
        .toList();
  }

  static Future<List<Place>> getPlaces(int tripId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/places');

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['places'] as List)
        .map((place) => Place.fromJson(Map<String, dynamic>.from(place)))
        .toList();
  }

  static Future<void> deletePlaces(int tripId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/places');

    final response = await http.delete(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<Place> createPlace({
    required int tripId,
    required Place place,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/places');

    final body = {
      'external_id': place.externalId,
      'source': place.source,

      'name': place.name,
      'city': place.city,
      'category': place.category,
      'address': place.address,

      'latitude': place.latitude,
      'longitude': place.longitude,
      'rating': place.rating,

      'opening_hours': place.openingHours,

      'opening_time': place.openingTime,
      'closing_time': place.closingTime,
      'visit_duration': place.visitDuration,
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

    return Place.fromJson(Map<String, dynamic>.from(data['place']));
  }
}
