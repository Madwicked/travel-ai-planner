import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../models/hotel.dart';
import '../services/hotel_service.dart';

class HotelOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const HotelOptionsPage({super.key, required this.trip});

  @override
  State<HotelOptionsPage> createState() => _HotelOptionsPageState();
}

class _HotelOptionsPageState extends State<HotelOptionsPage> {
  List<Hotel> options = [];

  bool isLoading = true;
  String? errorMessage;

  final TextEditingController searchController = TextEditingController();

  final TextEditingController minPriceController = TextEditingController();

  final TextEditingController maxPriceController = TextEditingController();

  Future<void> loadHotelOptions() async {
    final tripId = widget.trip['id'];

    try {
      final loadedOptions = await HotelService.getHotelOptions(tripId);

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
  void dispose() {
    searchController.dispose();
    minPriceController.dispose();
    maxPriceController.dispose();
    super.dispose();
  }

  List<Hotel> get filteredOptions {
    final searchText = searchController.text.trim().toLowerCase();

    final minPrice = double.tryParse(minPriceController.text.trim());

    final maxPrice = double.tryParse(maxPriceController.text.trim());

    return options.where((option) {
      final matchesSearch =
          searchText.isEmpty || option.name.toLowerCase().contains(searchText);

      final matchesMinPrice =
          minPrice == null || option.pricePerNight >= minPrice;

      final matchesMaxPrice =
          maxPrice == null || option.pricePerNight <= maxPrice;

      return matchesSearch && matchesMinPrice && matchesMaxPrice;
    }).toList();
  }

  void clearFilters() {
    searchController.clear();
    minPriceController.clear();
    maxPriceController.clear();

    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: Text(
          context.tr('Hotel Options'),
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: _buildBody(destination),
    );
  }

  Widget _buildBody(String destination) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            errorMessage!,
            style: const TextStyle(fontSize: 16),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    final filtered = filteredOptions;

    final destinationCurrency = widget.trip['destination_currency'] ?? 'EUR';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            destination,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 8),

          Text(
            'Choose where you want to stay',
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
          ),

          const SizedBox(height: 24),

          TextField(
            controller: searchController,
            onChanged: (_) {
              setState(() {});
            },
            decoration: InputDecoration(
              labelText: 'Search hotels',
              hintText: 'Hotel name',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: searchController.text.isNotEmpty
                  ? IconButton(
                      onPressed: () {
                        searchController.clear();
                        setState(() {});
                      },
                      icon: const Icon(Icons.clear),
                    )
                  : null,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),

          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: minPriceController,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  onChanged: (_) {
                    setState(() {});
                  },
                  decoration: InputDecoration(
                    labelText: 'From per night €',
                    hintText: 'Min',
                    prefixIcon: const Icon(Icons.euro),
                    suffixIcon: minPriceController.text.isNotEmpty
                        ? IconButton(
                            onPressed: () {
                              minPriceController.clear();
                              setState(() {});
                            },
                            icon: const Icon(Icons.clear),
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),

              const SizedBox(width: 12),

              Expanded(
                child: TextField(
                  controller: maxPriceController,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  onChanged: (_) {
                    setState(() {});
                  },
                  decoration: InputDecoration(
                    labelText: 'To per night €',
                    hintText: 'Max',
                    prefixIcon: const Icon(Icons.euro),
                    suffixIcon: maxPriceController.text.isNotEmpty
                        ? IconButton(
                            onPressed: () {
                              maxPriceController.clear();
                              setState(() {});
                            },
                            icon: const Icon(Icons.clear),
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          if (searchController.text.isNotEmpty ||
              minPriceController.text.isNotEmpty ||
              maxPriceController.text.isNotEmpty)
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: clearFilters,
                child: const Text('Clear filters'),
              ),
            ),

          const SizedBox(height: 12),

          if (filtered.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 32),
              child: Center(
                child: Text(
                  'No hotels match your filters.',
                  style: TextStyle(fontSize: 16),
                  textAlign: TextAlign.center,
                ),
              ),
            )
          else
            ...filtered.map(
              (option) => Card(
                margin: const EdgeInsets.only(bottom: 16),
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: () {
                    Navigator.pop(context, option);
                  },
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
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
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                option.name,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),

                              const SizedBox(height: 6),

                              Text(
                                option.city,
                                style: const TextStyle(fontSize: 15),
                              ),

                              const SizedBox(height: 4),

                              Text(
                                option.address,
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey.shade600,
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
                                style: const TextStyle(fontSize: 15),
                              ),

                              const SizedBox(height: 4),

                              Text(
                                '${option.nights} '
                                '${option.nights == 1 ? 'night' : 'nights'}',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(width: 8),

                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              '${option.destinationPrice} $destinationCurrency',
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${option.userPrice} ${option.userCurrency}',
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey.shade600,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${option.pricePerNight} ${option.currency}/night',
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey.shade600,
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
