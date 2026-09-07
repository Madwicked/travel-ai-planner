import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import '../models/hotel.dart';

class HotelService {
  static Future<List<Hotel>> getHotelOptions(int tripId) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/hotels/options',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception(
        'Server error: ${response.statusCode}',
      );
    }

    final data = jsonDecode(response.body);

    return (data['options'] as List)
        .map(
          (hotel) => Hotel.fromJson(
            Map<String, dynamic>.from(hotel),
          ),
        )
        .toList();
  }

  static Future<Hotel> createHotel({
    required int tripId,
    required Hotel hotel,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/hotels',
    );

    final body = {
      'name': hotel.name,
      'city': hotel.city,
      'address': hotel.address,
      'price_per_night': hotel.pricePerNight,
      'nights': hotel.nights,
      'total_price': hotel.totalPrice,
      'check_in': hotel.checkIn
          .toIso8601String()
          .split('T')
          .first,
      'check_out': hotel.checkOut
          .toIso8601String()
          .split('T')
          .first,
    };

    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Server error: ${response.statusCode}',
      );
    }

    final data = jsonDecode(response.body);

    return Hotel.fromJson(
      Map<String, dynamic>.from(data['hotel']),
    );
  }

  static Future<List<Hotel>> getHotels(int tripId) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/hotels',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception(
        'Server error: ${response.statusCode}',
      );
    }

    final data = jsonDecode(response.body);

    return (data['hotels'] as List)
        .map(
          (hotel) => Hotel.fromJson(
            Map<String, dynamic>.from(hotel),
          ),
        )
        .toList();
  }
}