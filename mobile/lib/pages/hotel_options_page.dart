import 'package:flutter/material.dart';

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

  String? selectedMeal;
  String? selectedAccommodationType;

  bool refundableOnly = false;
  bool petsAllowedOnly = false;
  bool adultsOnly = false;

  String sortOption = 'price';

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

  Future<void> selectHotelRate(Hotel hotel) async {
    if (hotel.rateOptions.isEmpty) {
      Navigator.pop(context, hotel);
      return;
    }

    final selectedRate = await showModalBottomSheet<HotelRate>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  hotel.name,
                  style: const TextStyle(
                    fontSize: 21,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 6),

                Text(
                  'Choose room and meal plan',
                  style: TextStyle(color: Colors.grey.shade600),
                ),

                const SizedBox(height: 16),

                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: hotel.rateOptions.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final rate = hotel.rateOptions[index];

                      return Card(
                        child: InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: () {
                            Navigator.pop(context, rate);
                          },
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  rate.roomName,
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),

                                if (rate.boardName.isNotEmpty)
                                  Padding(
                                    padding: const EdgeInsets.only(top: 5),
                                    child: Text(
                                      rate.boardName,
                                      style: TextStyle(
                                        color: Colors.grey.shade700,
                                      ),
                                    ),
                                  ),

                                const SizedBox(height: 8),

                                Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      '${rate.pricePerNight.toStringAsFixed(2)} '
                                      '${rate.currency}/night',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    Text(
                                      '${rate.totalPrice.toStringAsFixed(2)} '
                                      '${rate.currency}',
                                      style: const TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),

                                const SizedBox(height: 8),

                                Wrap(
                                  spacing: 6,
                                  runSpacing: 6,
                                  children: [
                                    Chip(
                                      label: Text(
                                        rate.refundable
                                            ? 'Refundable'
                                            : 'Non-refundable',
                                      ),
                                      visualDensity: VisualDensity.compact,
                                    ),

                                    if (rate.taxesIncluded)
                                      const Chip(
                                        label: Text('Taxes included'),
                                        visualDensity: VisualDensity.compact,
                                      ),
                                  ],
                                ),

                                if (rate.cancellationPolicies.isNotEmpty)
                                  const Padding(
                                    padding: EdgeInsets.only(top: 6),
                                    child: Text(
                                      'Cancellation policy available',
                                      style: TextStyle(fontSize: 12),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
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
    loadHotelOptions();
  }

  @override
  void dispose() {
    searchController.dispose();
    minPriceController.dispose();
    maxPriceController.dispose();
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

    final minPrice = double.tryParse(minPriceController.text.trim());

    final maxPrice = double.tryParse(maxPriceController.text.trim());

    final filtered = options.where((option) {
      final matchesSearch =
          searchText.isEmpty || option.name.toLowerCase().contains(searchText);

      final matchesMinPrice =
          minPrice == null || option.pricePerNight >= minPrice;

      final matchesMaxPrice =
          maxPrice == null || option.pricePerNight <= maxPrice;

      final matchesMeal =
          selectedMeal == null || hotelHasMeal(option, selectedMeal!);

      final matchesRefundable =
          !refundableOnly || hotelHasRefundableRate(option);

      final matchesPets = !petsAllowedOnly || option.petsAllowed == true;

      final matchesAdultsOnly = !adultsOnly || option.adultsOnly == true;

      final matchesAccommodation =
          selectedAccommodationType == null ||
          option.accommodationType?.toLowerCase() ==
              selectedAccommodationType!.toLowerCase();

      return matchesSearch &&
          matchesMinPrice &&
          matchesMaxPrice &&
          matchesMeal &&
          matchesRefundable &&
          matchesPets &&
          matchesAdultsOnly &&
          matchesAccommodation;
    }).toList();

    switch (sortOption) {
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

  bool get hasActiveFilters {
    return searchController.text.isNotEmpty ||
        minPriceController.text.isNotEmpty ||
        maxPriceController.text.isNotEmpty ||
        selectedMeal != null ||
        selectedAccommodationType != null ||
        refundableOnly ||
        petsAllowedOnly ||
        adultsOnly ||
        sortOption != 'price';
  }

  void clearFilters() {
    searchController.clear();
    minPriceController.clear();
    maxPriceController.clear();

    setState(() {
      selectedMeal = null;
      selectedAccommodationType = null;
      refundableOnly = false;
      petsAllowedOnly = false;
      adultsOnly = false;
      sortOption = 'price';
    });
  }

  void showFilters() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return SafeArea(
              child: Padding(
                padding: EdgeInsets.only(
                  left: 20,
                  right: 20,
                  top: 8,
                  bottom: MediaQuery.of(context).viewInsets.bottom + 20,
                ),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Filters',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      const SizedBox(height: 20),

                      const Text(
                        'Meals',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 8),

                      DropdownButtonFormField<String>(
                        initialValue: selectedMeal,
                        decoration: InputDecoration(
                          labelText: 'Meal plan',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        items: [
                          const DropdownMenuItem<String>(
                            value: null,
                            child: Text('Any meal plan'),
                          ),
                          ...availableMeals.map(
                            (meal) => DropdownMenuItem<String>(
                              value: meal,
                              child: Text(meal),
                            ),
                          ),
                        ],
                        onChanged: (value) {
                          setModalState(() {
                            selectedMeal = value;
                          });

                          setState(() {});
                        },
                      ),

                      const SizedBox(height: 20),

                      const Text(
                        'Accommodation type',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 8),

                      DropdownButtonFormField<String>(
                        initialValue: selectedAccommodationType,
                        decoration: InputDecoration(
                          labelText: 'Type',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        items: [
                          const DropdownMenuItem<String>(
                            value: null,
                            child: Text('Any type'),
                          ),
                          ...availableAccommodationTypes.map(
                            (type) => DropdownMenuItem<String>(
                              value: type,
                              child: Text(
                                type,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ),
                        ],
                        onChanged: (value) {
                          setModalState(() {
                            selectedAccommodationType = value;
                          });

                          setState(() {});
                        },
                      ),

                      const SizedBox(height: 12),

                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Refundable only'),
                        value: refundableOnly,
                        onChanged: (value) {
                          setModalState(() {
                            refundableOnly = value ?? false;
                          });

                          setState(() {});
                        },
                      ),

                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Pets allowed'),
                        value: petsAllowedOnly,
                        onChanged: (value) {
                          setModalState(() {
                            petsAllowedOnly = value ?? false;
                          });

                          setState(() {});
                        },
                      ),

                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Adults only'),
                        value: adultsOnly,
                        onChanged: (value) {
                          setModalState(() {
                            adultsOnly = value ?? false;
                          });

                          setState(() {});
                        },
                      ),

                      const SizedBox(height: 12),

                      const Text(
                        'Sort by',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 8),

                      RadioListTile<String>(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Price: low to high'),
                        value: 'price',
                        groupValue: sortOption,
                        onChanged: (value) {
                          setModalState(() {
                            sortOption = value!;
                          });

                          setState(() {});
                        },
                      ),

                      RadioListTile<String>(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Price: high to low'),
                        value: 'price_desc',
                        groupValue: sortOption,
                        onChanged: (value) {
                          setModalState(() {
                            sortOption = value!;
                          });

                          setState(() {});
                        },
                      ),

                      RadioListTile<String>(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Category: highest first'),
                        subtitle: const Text('Based on hotel category / stars'),
                        value: 'rating',
                        groupValue: sortOption,
                        onChanged: (value) {
                          setModalState(() {
                            sortOption = value!;
                          });

                          setState(() {});
                        },
                      ),

                      RadioListTile<String>(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Category + price'),
                        subtitle: const Text(
                          'Higher category first, then cheaper',
                        ),
                        value: 'rating_price',
                        groupValue: sortOption,
                        onChanged: (value) {
                          setModalState(() {
                            sortOption = value!;
                          });

                          setState(() {});
                        },
                      ),

                      const SizedBox(height: 12),

                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: () {
                            Navigator.pop(context);
                            setState(() {});
                          },
                          child: const Text('Apply filters'),
                        ),
                      ),

                      const SizedBox(height: 8),

                      SizedBox(
                        width: double.infinity,
                        child: TextButton(
                          onPressed: () {
                            selectedMeal = null;
                            selectedAccommodationType = null;
                            refundableOnly = false;
                            petsAllowedOnly = false;
                            adultsOnly = false;
                            sortOption = 'price';

                            setModalState(() {});

                            setState(() {});

                            Navigator.pop(context);
                          },
                          child: const Text('Reset filters'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
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

          if (hasActiveFilters)
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: clearFilters,
                child: const Text('Clear filters'),
              ),
            ),

          if (hasActiveFilters)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (selectedMeal != null) Chip(label: Text(selectedMeal!)),

                  if (selectedAccommodationType != null)
                    Chip(label: Text(selectedAccommodationType!)),

                  if (refundableOnly) const Chip(label: Text('Refundable')),

                  if (petsAllowedOnly) const Chip(label: Text('Pets allowed')),

                  if (adultsOnly) const Chip(label: Text('Adults only')),
                ],
              ),
            ),

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
                                    Text(
                                      option.categoryName!,
                                      style: const TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),

                              if (option.accommodationType != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    option.accommodationType!,
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Colors.grey.shade700,
                                    ),
                                  ),
                                ),

                              const SizedBox(height: 4),

                              Text(
                                option.city,
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
                                          ' • ${rate.pricePerNight.toStringAsFixed(2)} ${rate.currency}/night',
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
        ],
      ),
    );
  }
}
