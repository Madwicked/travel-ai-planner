import 'package:flutter/material.dart';

import '../models/hotel_filter_state.dart';

class HotelFiltersPage extends StatefulWidget {
  final HotelFilterState initialFilters;
  final List<String> availableMeals;
  final List<String> availableAccommodationTypes;

  const HotelFiltersPage({
    super.key,
    required this.initialFilters,
    required this.availableMeals,
    required this.availableAccommodationTypes,
  });

  @override
  State<HotelFiltersPage> createState() => _HotelFiltersPageState();
}

class _HotelFiltersPageState extends State<HotelFiltersPage> {
  late final TextEditingController minPriceController;
  late final TextEditingController maxPriceController;

  String? selectedMeal;
  String? selectedAccommodationType;

  bool refundableOnly = false;
  bool petsAllowedOnly = false;
  bool adultsOnly = false;

  String sortOption = 'price';

  @override
  void initState() {
    super.initState();

    final filters = widget.initialFilters;

    minPriceController = TextEditingController(
      text: filters.minPrice?.toString() ?? '',
    );

    maxPriceController = TextEditingController(
      text: filters.maxPrice?.toString() ?? '',
    );

    selectedMeal = filters.selectedMeal;
    selectedAccommodationType = filters.selectedAccommodationType;

    refundableOnly = filters.refundableOnly;
    petsAllowedOnly = filters.petsAllowedOnly;
    adultsOnly = filters.adultsOnly;

    sortOption = filters.sortOption;
  }

  @override
  void dispose() {
    minPriceController.dispose();
    maxPriceController.dispose();
    super.dispose();
  }

  double? _parsePrice(String value) {
    final normalized = value.trim().replaceAll(',', '.');

    if (normalized.isEmpty) {
      return null;
    }

    return double.tryParse(normalized);
  }

  void applyFilters() {
    final filters = HotelFilterState(
      minPrice: _parsePrice(minPriceController.text),
      maxPrice: _parsePrice(maxPriceController.text),
      selectedMeal: selectedMeal,
      selectedAccommodationType: selectedAccommodationType,
      refundableOnly: refundableOnly,
      petsAllowedOnly: petsAllowedOnly,
      adultsOnly: adultsOnly,
      sortOption: sortOption,
    );

    Navigator.pop(context, filters);
  }

  void resetFilters() {
    setState(() {
      minPriceController.clear();
      maxPriceController.clear();

      selectedMeal = null;
      selectedAccommodationType = null;

      refundableOnly = false;
      petsAllowedOnly = false;
      adultsOnly = false;

      sortOption = 'price';
    });
  }

  InputDecoration _compactDecoration({String? hintText, Widget? prefix}) {
    return InputDecoration(
      hintText: hintText,
      prefix: prefix,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Filters')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
        children: [
          Text(
            'Price per night',
            style: Theme.of(context).textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.w600),
          ),

          const SizedBox(height: 8),

          Row(
            children: [
              Expanded(
                child: Container(
                  height: 40,
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  child: Row(
                    children: [
                      const Text(
                        '€',
                        style: TextStyle(fontSize: 14, color: Colors.black),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: TextField(
                          controller: minPriceController,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          style: const TextStyle(fontSize: 14),
                          decoration: const InputDecoration(
                            hintText: 'Min price',
                            border: InputBorder.none,
                            isDense: true,
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(width: 10),

              Expanded(
                child: Container(
                  height: 40,
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  child: Row(
                    children: [
                      const Text(
                        '€',
                        style: TextStyle(fontSize: 14, color: Colors.black),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: TextField(
                          controller: maxPriceController,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          style: const TextStyle(fontSize: 14),
                          decoration: const InputDecoration(
                            hintText: 'Max price',
                            border: InputBorder.none,
                            isDense: true,
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          Text(
            'Meal plan',
            style: Theme.of(context).textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.w600),
          ),

          const SizedBox(height: 6),

          DropdownButtonFormField<String>(
            value: selectedMeal,
            isExpanded: true,
            decoration: _compactDecoration(hintText: 'Any meal plan'),
            items: [
              const DropdownMenuItem<String>(
                value: null,
                child: Text('Any meal plan'),
              ),
              ...widget.availableMeals.map(
                (meal) => DropdownMenuItem<String>(
                  value: meal,
                  child: Text(meal, overflow: TextOverflow.ellipsis),
                ),
              ),
            ],
            onChanged: (value) {
              setState(() {
                selectedMeal = value;
              });
            },
          ),

          const SizedBox(height: 16),

          Text(
            'Accommodation type',
            style: Theme.of(context).textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.w600),
          ),

          const SizedBox(height: 6),

          DropdownButtonFormField<String>(
            value: selectedAccommodationType,
            isExpanded: true,
            decoration: _compactDecoration(hintText: 'Any accommodation type'),
            items: [
              const DropdownMenuItem<String>(
                value: null,
                child: Text('Any accommodation type'),
              ),
              ...widget.availableAccommodationTypes.map(
                (type) => DropdownMenuItem<String>(
                  value: type,
                  child: Text(type, overflow: TextOverflow.ellipsis),
                ),
              ),
            ],
            onChanged: (value) {
              setState(() {
                selectedAccommodationType = value;
              });
            },
          ),

          const SizedBox(height: 12),

          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Refundable only'),
            value: refundableOnly,
            onChanged: (value) {
              setState(() {
                refundableOnly = value ?? false;
              });
            },
          ),

          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Pets allowed'),
            value: petsAllowedOnly,
            onChanged: (value) {
              setState(() {
                petsAllowedOnly = value ?? false;
              });
            },
          ),

          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Adults only'),
            value: adultsOnly,
            onChanged: (value) {
              setState(() {
                adultsOnly = value ?? false;
              });
            },
          ),

          const SizedBox(height: 12),

          Text(
            'Sort by',
            style: Theme.of(context).textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.w600),
          ),

          const SizedBox(height: 4),

          RadioListTile<String>(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Price: low to high'),
            value: 'price',
            groupValue: sortOption,
            onChanged: (value) {
              if (value == null) return;

              setState(() {
                sortOption = value;
              });
            },
          ),

          RadioListTile<String>(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Price: high to low'),
            value: 'price_desc',
            groupValue: sortOption,
            onChanged: (value) {
              if (value == null) return;

              setState(() {
                sortOption = value;
              });
            },
          ),

          RadioListTile<String>(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Rating'),
            value: 'rating',
            groupValue: sortOption,
            onChanged: (value) {
              if (value == null) return;

              setState(() {
                sortOption = value;
              });
            },
          ),

          RadioListTile<String>(
            contentPadding: EdgeInsets.zero,
            dense: true,
            visualDensity: VisualDensity.compact,
            title: const Text('Rating, then price'),
            value: 'rating_price',
            groupValue: sortOption,
            onChanged: (value) {
              if (value == null) return;

              setState(() {
                sortOption = value;
              });
            },
          ),

          const SizedBox(height: 16),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: applyFilters,
              child: const Text('Apply filters'),
            ),
          ),

          const SizedBox(height: 8),

          SizedBox(
            width: double.infinity,
            child: TextButton(
              onPressed: resetFilters,
              child: const Text('Reset filters'),
            ),
          ),
        ],
      ),
    );
  }
}
