import 'package:flutter/material.dart';

import '../models/hotel.dart';
import '../models/hotel_filter_state.dart';
import '../services/hotel_service.dart';
import 'hotel_filters_page.dart';
import 'hotel_rates_page.dart';

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

  final ScrollController _scrollController = ScrollController();
  bool _showScrollToTop = false;

  HotelFilterState filters = const HotelFilterState();

  int currentOffset = 0;
  int pageSize = 50;

  bool isLoadingMore = false;

  bool get hasMore => currentOffset < filteredOptions.length;

  Future<void> loadHotelOptions() async {
    final tripId = widget.trip['id'];

    try {
      final loadedOptions = await HotelService.getHotelOptions(tripId);

      if (!mounted) return;

      setState(() {
        options = loadedOptions;

        currentOffset = loadedOptions.length > pageSize
            ? pageSize
            : loadedOptions.length;

        isLoading = false;
        isLoadingMore = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = 'Failed to load hotel options';
        isLoading = false;
        isLoadingMore = false;
      });
    }
  }

  void loadMoreHotelOptions() {
    if (isLoadingMore || !hasMore) return;

    setState(() {
      isLoadingMore = true;

      currentOffset = (currentOffset + pageSize).clamp(
        0,
        filteredOptions.length,
      );

      isLoadingMore = false;
    });
  }

  Future<void> selectHotelRate(Hotel hotel) async {
    if (hotel.rateOptions.isEmpty) {
      Navigator.pop(context, hotel);
      return;
    }

    final selectedRate = await Navigator.push<HotelRate>(
      context,
      MaterialPageRoute(builder: (_) => HotelRatesPage(hotel: hotel)),
    );

    if (selectedRate == null || !mounted) {
      return;
    }

    final selectedHotel = hotel.copyWith(
      pricePerNight: selectedRate.pricePerNight,
      totalPrice: selectedRate.totalPrice,
      currency: selectedRate.currency,
      rateOptions: [selectedRate],
    );

    Navigator.pop(context, selectedHotel);
  }

  @override
  void initState() {
    super.initState();

    _scrollController.addListener(_handleScroll);

    loadHotelOptions();
  }

  void _handleScroll() {
    if (!_scrollController.hasClients) {
      return;
    }

    final shouldShow = _scrollController.offset > 500;

    if (shouldShow != _showScrollToTop) {
      setState(() {
        _showScrollToTop = shouldShow;
      });
    }
  }

  void _scrollToTop() {
    _scrollController.animateTo(
      0,
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeOut,
    );
  }

  @override
  void dispose() {
    _scrollController.removeListener(_handleScroll);
    _scrollController.dispose();
    searchController.dispose();
    super.dispose();
  }

  List<String> get availableMeals {
    final meals = <String>{};

    for (final hotel in options) {
      for (final rate in hotel.rateOptions) {
        final boardName = rate.boardName.trim();

        if (boardName.isNotEmpty) {
          meals.add(boardName);
        }
      }
    }

    final result = meals.toList();
    result.sort();

    return result;
  }

  List<String> get availableAccommodationTypes {
    final types = <String>{};

    for (final hotel in options) {
      final type = hotel.accommodationType?.trim();

      if (type != null && type.isNotEmpty) {
        types.add(type);
      }
    }

    final result = types.toList();
    result.sort();

    return result;
  }

  bool hotelHasMeal(Hotel hotel, String meal) {
    return hotel.rateOptions.any((rate) => rate.boardName.trim() == meal);
  }

  bool hotelHasRefundableRate(Hotel hotel) {
    return hotel.rateOptions.any((rate) => rate.refundable);
  }

  int getHotelStars(Hotel hotel) {
    final category = hotel.categoryName?.toUpperCase() ?? '';

    final match = RegExp(r'(\d+)').firstMatch(category);

    if (match != null) {
      return int.tryParse(match.group(1)!) ?? 0;
    }

    final code = hotel.categoryCode?.toUpperCase() ?? '';

    final codeMatch = RegExp(r'(\d+)').firstMatch(code);

    if (codeMatch != null) {
      return int.tryParse(codeMatch.group(1)!) ?? 0;
    }

    return 0;
  }

  List<Hotel> get filteredOptions {
    final searchText = searchController.text.trim().toLowerCase();

    final minPrice = filters.minPrice;
    final maxPrice = filters.maxPrice;

    final filtered = options.where((option) {
      final matchesSearch =
          searchText.isEmpty || option.name.toLowerCase().contains(searchText);

      final matchesMinPrice =
          minPrice == null || option.pricePerNight >= minPrice;

      final matchesMaxPrice =
          maxPrice == null || option.pricePerNight <= maxPrice;

      final matchesMeal =
          filters.selectedMeal == null ||
          hotelHasMeal(option, filters.selectedMeal!);

      final matchesRefundable =
          !filters.refundableOnly || hotelHasRefundableRate(option);

      final matchesPets =
          !filters.petsAllowedOnly || option.petsAllowed == true;

      final matchesAdultsOnly =
          !filters.adultsOnly || option.adultsOnly == true;

      final matchesAccommodation =
          filters.selectedAccommodationType == null ||
          option.accommodationType?.toLowerCase() ==
              filters.selectedAccommodationType!.toLowerCase();

      return matchesSearch &&
          matchesMinPrice &&
          matchesMaxPrice &&
          matchesMeal &&
          matchesRefundable &&
          matchesPets &&
          matchesAdultsOnly &&
          matchesAccommodation;
    }).toList();

    switch (filters.sortOption) {
      case 'price':
        filtered.sort((a, b) => a.pricePerNight.compareTo(b.pricePerNight));
        break;

      case 'price_desc':
        filtered.sort((a, b) => b.pricePerNight.compareTo(a.pricePerNight));
        break;

      case 'rating':
        filtered.sort((a, b) => getHotelStars(b).compareTo(getHotelStars(a)));
        break;

      case 'rating_price':
        filtered.sort((a, b) {
          final starsA = getHotelStars(a);
          final starsB = getHotelStars(b);

          if (starsA != starsB) {
            return starsB.compareTo(starsA);
          }

          return a.pricePerNight.compareTo(b.pricePerNight);
        });
        break;
    }

    return filtered;
  }

  List<Hotel> get visibleOptions {
    final end = currentOffset.clamp(0, filteredOptions.length);

    return filteredOptions.take(end).toList();
  }

  bool get hasActiveFilters {
    return searchController.text.isNotEmpty || filters.hasActiveFilters;
  }

  void clearFilters() {
    searchController.clear();

    setState(() {
      filters = const HotelFilterState();
      currentOffset = 0;
      isLoading = true;
      errorMessage = null;
    });

    loadHotelOptions();
  }

  Future<void> showFilters() async {
    final result = await Navigator.push<HotelFilterState>(
      context,
      MaterialPageRoute(
        builder: (_) => HotelFiltersPage(
          initialFilters: filters,
          availableMeals: availableMeals,
          availableAccommodationTypes: availableAccommodationTypes,
        ),
      ),
    );

    if (result == null || !mounted) {
      return;
    }

    setState(() {
      filters = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Hotel Options',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            onPressed: showFilters,
            icon: const Icon(Icons.tune),
            tooltip: 'Filters',
          ),
        ],
      ),
      body: _buildBody(destination),
      floatingActionButton: _showScrollToTop
          ? FloatingActionButton(
              onPressed: _scrollToTop,
              child: const Icon(Icons.keyboard_arrow_up),
            )
          : null,
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
    final visible = visibleOptions;

    return SingleChildScrollView(
      controller: _scrollController,
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

          const SizedBox(height: 12),

          if (hasActiveFilters) ...[
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: clearFilters,
                child: const Text('Clear filters'),
              ),
            ),

            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (filters.minPrice != null)
                    Chip(label: Text('From €${filters.minPrice}')),

                  if (filters.maxPrice != null)
                    Chip(label: Text('To €${filters.maxPrice}')),

                  if (filters.selectedMeal != null)
                    Chip(label: Text(filters.selectedMeal!)),

                  if (filters.selectedAccommodationType != null)
                    Chip(label: Text(filters.selectedAccommodationType!)),

                  if (filters.refundableOnly)
                    const Chip(label: Text('Refundable')),

                  if (filters.petsAllowedOnly)
                    const Chip(label: Text('Pets allowed')),

                  if (filters.adultsOnly)
                    const Chip(label: Text('Adults only')),
                ],
              ),
            ),
          ],

          Text(
            hasActiveFilters
                ? '${filtered.length} of ${options.length} hotels found'
                : '${filtered.length} hotels found',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),

          const SizedBox(height: 10),

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
            ...visible.map(
              (option) => Card(
                margin: const EdgeInsets.only(bottom: 16),
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: () {
                    selectHotelRate(option);
                  },
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.blue.withValues(alpha: 0.1),
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
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),

                              const SizedBox(height: 6),

                              if (option.categoryName != null)
                                Row(
                                  children: [
                                    const Icon(
                                      Icons.star,
                                      size: 16,
                                      color: Colors.amber,
                                    ),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Text(
                                        option.categoryName!,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),

                              if (option.accommodationType != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    option.accommodationType!,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Colors.grey.shade700,
                                    ),
                                  ),
                                ),

                              const SizedBox(height: 4),

                              Text(
                                option.city,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontSize: 15),
                              ),

                              const SizedBox(height: 4),

                              Text(
                                option.address,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey.shade600,
                                ),
                              ),

                              const SizedBox(height: 10),

                              Wrap(
                                spacing: 6,
                                runSpacing: 6,
                                children: [
                                  if (option.adultsOnly == true)
                                    const Chip(
                                      label: Text('Adults only'),
                                      visualDensity: VisualDensity.compact,
                                    ),

                                  if (option.petsAllowed == true)
                                    const Chip(
                                      label: Text('Pets'),
                                      visualDensity: VisualDensity.compact,
                                    ),

                                  if (hotelHasRefundableRate(option))
                                    const Chip(
                                      label: Text('Refundable'),
                                      visualDensity: VisualDensity.compact,
                                    ),
                                ],
                              ),

                              const SizedBox(height: 10),

                              Text(
                                '${option.checkIn.day.toString().padLeft(2, '0')}.'
                                '${option.checkIn.month.toString().padLeft(2, '0')}.'
                                '${option.checkIn.year} → '
                                '${option.checkOut.day.toString().padLeft(2, '0')}.'
                                '${option.checkOut.month.toString().padLeft(2, '0')}.'
                                '${option.checkOut.year}',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
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

                              if (option.rateOptions.isNotEmpty) ...[
                                const SizedBox(height: 14),

                                const Text(
                                  'Available rates',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),

                                const SizedBox(height: 6),

                                ...option.rateOptions
                                    .take(3)
                                    .map(
                                      (rate) => Padding(
                                        padding: const EdgeInsets.only(
                                          bottom: 4,
                                        ),
                                        child: Text(
                                          '${rate.roomName}'
                                          '${rate.boardName.isNotEmpty ? ' • ${rate.boardName}' : ''}'
                                          ' • ${rate.pricePerNight.toStringAsFixed(2)} '
                                          '${rate.currency}/night',
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.grey.shade700,
                                          ),
                                        ),
                                      ),
                                    ),
                              ],
                            ],
                          ),
                        ),

                        const SizedBox(width: 8),

                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              '${option.userPrice.toStringAsFixed(2)} '
                              '${option.userCurrency}',
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${option.destinationPrice.toStringAsFixed(2)} '
                              '${option.destinationCurrency}',
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey.shade600,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${option.pricePerNight.toStringAsFixed(2)} '
                              '${option.currency}/night',
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

          if (hasMore && visible.isNotEmpty) ...[
            const SizedBox(height: 16),
            Center(
              child: isLoadingMore
                  ? const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: CircularProgressIndicator(),
                    )
                  : ElevatedButton(
                      onPressed: loadMoreHotelOptions,
                      child: const Text('View more'),
                    ),
            ),
          ],

          const SizedBox(height: 80),
        ],
      ),
    );
  }
}
