import 'package:flutter/material.dart';

import '../models/place.dart';
import '../services/place_service.dart';

class PlaceOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const PlaceOptionsPage({
    super.key,
    required this.trip,
  });

  @override
  State<PlaceOptionsPage> createState() =>
      _PlaceOptionsPageState();
}

class _PlaceOptionsPageState
    extends State<PlaceOptionsPage> {
  List<Place> options = [];
  final Set<int> selectedIndexes = {};

  bool isLoading = true;
  String? errorMessage;

  Future<void> loadPlaceOptions() async {
    final tripId = widget.trip['id'];

    try {
      final loadedOptions =
          await PlaceService.getPlaceOptions(tripId);

      if (!mounted) return;

      setState(() {
        options = loadedOptions;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage =
            'Failed to load place options';
        isLoading = false;
      });
    }
  }

  IconData getPlaceIcon(String category) {
    switch (category) {
      case 'Culture':
        return Icons.account_balance;
      case 'Nature':
        return Icons.park;
      case 'Sightseeing':
        return Icons.photo_camera;
      default:
        return Icons.place;
    }
  }

  void togglePlace(int index) {
    setState(() {
      if (selectedIndexes.contains(index)) {
        selectedIndexes.remove(index);
      } else {
        selectedIndexes.add(index);
      }
    });
  }

  void savePlaces() {
    final selectedPlaces = selectedIndexes
        .map((index) => options[index])
        .toList();

    Navigator.pop(
      context,
      selectedPlaces,
    );
  }

  @override
  void initState() {
    super.initState();
    loadPlaceOptions();
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Places to Visit',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: _buildBody(destination),
      bottomNavigationBar: isLoading
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: selectedIndexes.isEmpty
                        ? null
                        : savePlaces,
                    child: Text(
                      selectedIndexes.isEmpty
                          ? 'Save Places'
                          : 'Save Places (${selectedIndexes.length})',
                    ),
                  ),
                ),
              ),
            ),
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
      padding: const EdgeInsets.fromLTRB(
        20,
        20,
        20,
        100,
      ),
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
            'Choose places you want to visit',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 28),
          ...options.asMap().entries.map(
            (entry) {
              final index = entry.key;
              final option = entry.value;
              final isSelected =
                  selectedIndexes.contains(index);

              return Card(
                margin: const EdgeInsets.only(
                  bottom: 16,
                ),
                elevation: isSelected ? 4 : 2,
                shape: RoundedRectangleBorder(
                  borderRadius:
                      BorderRadius.circular(16),
                  side: isSelected
                      ? const BorderSide(
                          color: Colors.blue,
                          width: 2,
                        )
                      : BorderSide.none,
                ),
                child: InkWell(
                  borderRadius:
                      BorderRadius.circular(16),
                  onTap: () => togglePlace(index),
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
                          child: Icon(
                            getPlaceIcon(
                              option.category,
                            ),
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
                                option.category,
                                style:
                                    const TextStyle(
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(height: 6),
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
                                'Open: '
                                '${option.openingTime}'
                                '–'
                                '${option.closingTime}',
                                style:
                                    const TextStyle(
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Visit: '
                                '${option.visitDuration ?? '-'}',
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
                        Checkbox(
                          value: isSelected,
                          onChanged: (_) =>
                              togglePlace(index),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
