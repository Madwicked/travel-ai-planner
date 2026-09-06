import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class HotelOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const HotelOptionsPage({
    super.key,
    required this.trip,
  });

  @override
  State<HotelOptionsPage> createState() =>
      _HotelOptionsPageState();
}

class _HotelOptionsPageState
    extends State<HotelOptionsPage> {
  List<Map<String, dynamic>> options = [];

  bool isLoading = true;
  String? errorMessage;

  String formatDateForDisplay(String date) {
    final parts = date.split('-');

    if (parts.length != 3) {
      return date;
    }

    return '${parts[2]}.${parts[1]}.${parts[0]}';
  }

  Future<void> loadHotelOptions() async {
    final tripId = widget.trip['id'];

    try {
      final response = await http.get(
        Uri.parse(
          'http://10.0.2.2:8000/api/trips/$tripId/hotels/options',
        ),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Failed to load hotel options',
        );
      }

      final data = jsonDecode(response.body);

      final loadedOptions =
          List<Map<String, dynamic>>.from(
        data['options'],
      );

      if (!mounted) return;

      setState(() {
        options = loadedOptions;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = 'Failed to load hotel options';
        isLoading = false;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    loadHotelOptions();
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Hotel Options',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: _buildBody(destination),
    );
  }

  Widget _buildBody(String destination) {
    if (isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            errorMessage!,
            style: const TextStyle(
              fontSize: 16,
            ),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            destination,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 8),

          Text(
            'Choose where you want to stay',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade600,
            ),
          ),

          const SizedBox(height: 28),

          ...options.map(
            (option) => Card(
              margin: const EdgeInsets.only(
                bottom: 16,
              ),
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.circular(16),
              ),
              child: InkWell(
                borderRadius:
                    BorderRadius.circular(16),
                onTap: () {
                  Navigator.pop(
                    context,
                    option,
                  );
                },
                child: Padding(
                  padding:
                      const EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding:
                            const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.blue
                              .withOpacity(0.1),
                          borderRadius:
                              BorderRadius.circular(
                            12,
                          ),
                        ),
                        child: const Icon(
                          Icons.hotel,
                          color: Colors.blue,
                          size: 28,
                        ),
                      ),

                      const SizedBox(width: 16),

                      Expanded(
                        child: Column(
                          crossAxisAlignment:
                              CrossAxisAlignment.start,
                          children: [
                            Text(
                              option['name']
                                  as String,
                              style:
                                  const TextStyle(
                                fontSize: 18,
                                fontWeight:
                                    FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 6),

                            Text(
                              option['city']
                                  as String,
                              style: const TextStyle(
                                fontSize: 15,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              option['address']
                                  as String,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),

                            const SizedBox(height: 10),

                            Text(
                              '${formatDateForDisplay(
                                option['check_in']
                                    as String,
                              )} → '
                              '${formatDateForDisplay(
                                option['check_out']
                                    as String,
                              )}',
                              style:
                                  const TextStyle(
                                fontSize: 15,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${option['nights']} '
                              '${option['nights'] == 1 ? 'night' : 'nights'}',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(width: 8),

                      Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.end,
                        children: [
                          Text(
                            '€${option['total_price']}',
                            style:
                                const TextStyle(
                              fontSize: 20,
                              fontWeight:
                                  FontWeight.bold,
                            ),
                          ),

                          const SizedBox(height: 4),

                          Text(
                            '€${option['price_per_night']}/night',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors
                                  .grey
                                  .shade600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}