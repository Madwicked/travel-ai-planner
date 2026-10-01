import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import '../models/place.dart';

class PlaceOptionsResult {
  final List<Place> options;
  final int total;
  final bool hasMore;

  PlaceOptionsResult({
    required this.options,
    required this.total,
    required this.hasMore,
  });
}

class PlaceService {
  static Future<PlaceOptionsResult> getPlaceOptions({
    required int tripId,
    required int stopId,
    int? radiusKm,
    String? search,
    String searchType = 'city',
    String? category,
    int offset = 0,
    int limit = 50,
  }) async {
    final queryParameters = <String, String>{
      'offset': offset.toString(),
      'limit': limit.toString(),
      'search_type': searchType,
      'stop_id': stopId.toString(),
    };

    if (radiusKm != null && searchType == 'city') {
      queryParameters['radius_km'] = radiusKm.toString();
    }

    if (search != null && search.trim().isNotEmpty) {
      queryParameters['search'] = search.trim();
    }

    if (category != null && category != 'All') {
      queryParameters['category'] = category.toLowerCase();
    }

    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/places/options',
    ).replace(queryParameters: queryParameters);

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return PlaceOptionsResult(
      options: (data['options'] as List)
          .map((place) => Place.fromJson(Map<String, dynamic>.from(place)))
          .toList(),
      total: data['total'] as int,
      hasMore: data['has_more'] as bool? ?? false,
    );
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

  static Future<void> deletePlaces({
    required int tripId,
    required int stopId,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/places?stop_id=$stopId',
    );

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
      'stop_id': place.stopId,
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

  static Future<List<Place>> createPlacesBulk({
    required int tripId,
    required List<Place> places,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/places/bulk');

    final body = places.map((place) {
      return {
        'stop_id': place.stopId,
        'external_id': place.externalId,
        'source': place.source,

        'name': place.name,
        'city': place.city,
        'country': place.country,
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
    }).toList();

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['places'] as List)
        .map((place) => Place.fromJson(Map<String, dynamic>.from(place)))
        .toList();
  }

  static Future<void> deletePlace({
    required int tripId,
    required int placeId,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/places/$placeId',
    );

    final response = await http.delete(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }
  }
}
