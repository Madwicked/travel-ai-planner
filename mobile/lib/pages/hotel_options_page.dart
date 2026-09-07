import 'package:flutter/material.dart';

import '../models/hotel.dart';
import '../services/hotel_service.dart';

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
  List<Hotel> options = [];

  bool isLoading = true;
  String? errorMessage;

  Future<void> loadHotelOptions() async {
    final tripId = widget.trip['id'];

    try {
      final loadedOptions =
          await HotelService.getHotelOptions(tripId);

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
                              option.name,
                              style:
                                  const TextStyle(
                                fontSize: 18,
                                fontWeight:
                                    FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 6),

                            Text(
                              option.city,
                              style: const TextStyle(
                                fontSize: 15,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              option.address,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),

                            const SizedBox(height: 10),

                            Text(
                              '${option.checkIn.day.toString().padLeft(2, '0')}.'
                              '${option.checkIn.month.toString().padLeft(2, '0')}.'
                              '${option.checkIn.year} → '
                              '${option.checkOut.day.toString().padLeft(2, '0')}.'
                              '${option.checkOut.month.toString().padLeft(2, '0')}.'
                              '${option.checkOut.year}',
                              style:
                                  const TextStyle(
                                fontSize: 15,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${option.nights} '
                              '${option.nights == 1 ? 'night' : 'nights'}',
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
                            '€${option.totalPrice}',
                            style:
                                const TextStyle(
                              fontSize: 20,
                              fontWeight:
                                  FontWeight.bold,
                            ),
                          ),

                          const SizedBox(height: 4),

                          Text(
                            '€${option.pricePerNight}/night',
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

