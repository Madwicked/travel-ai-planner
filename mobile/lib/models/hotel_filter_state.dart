class HotelFilterState {
  final double? minPrice;
  final double? maxPrice;
  final String? selectedMeal;
  final String? selectedAccommodationType;
  final bool refundableOnly;
  final bool petsAllowedOnly;
  final bool adultsOnly;
  final String sortOption;

  const HotelFilterState({
    this.minPrice,
    this.maxPrice,
    this.selectedMeal,
    this.selectedAccommodationType,
    this.refundableOnly = false,
    this.petsAllowedOnly = false,
    this.adultsOnly = false,
    this.sortOption = 'price',
  });

  bool get hasActiveFilters {
    return minPrice != null ||
        maxPrice != null ||
        selectedMeal != null ||
        selectedAccommodationType != null ||
        refundableOnly ||
        petsAllowedOnly ||
        adultsOnly ||
        sortOption != 'price';
  }
}
