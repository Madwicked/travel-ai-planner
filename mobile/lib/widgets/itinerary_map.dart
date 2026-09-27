import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class ItineraryMap extends StatefulWidget {
  final Map<String, dynamic>? hotel;
  final List<Map<String, dynamic>> places;
  final List<Map<String, dynamic>> airports;

  const ItineraryMap({
    super.key,
    this.hotel,
    required this.places,
    this.airports = const [],
  });

  @override
  State<ItineraryMap> createState() => _ItineraryMapState();
}

class _ItineraryMapState extends State<ItineraryMap> {
  final MapController mapController = MapController();

  List<Marker> get markers {
    final result = <Marker>[];

    final hotel = widget.hotel;

    if (hotel != null &&
        hotel['latitude'] != null &&
        hotel['longitude'] != null) {
      result.add(
        Marker(
          point: LatLng(
            (hotel['latitude'] as num).toDouble(),
            (hotel['longitude'] as num).toDouble(),
          ),
          width: 150,
          height: 90,
          alignment: Alignment.topCenter,
          child: _buildMarker(
            icon: Icons.hotel,
            color: Colors.orange,
            label: hotel['name']?.toString() ?? 'Hotel',
          ),
        ),
      );
    }

    for (final airport in widget.airports) {
      if (airport['latitude'] == null || airport['longitude'] == null) {
        continue;
      }

      final code = airport['code']?.toString() ?? '';
      final label = airport['label']?.toString() ?? 'Airport';

      result.add(
        Marker(
          point: LatLng(
            (airport['latitude'] as num).toDouble(),
            (airport['longitude'] as num).toDouble(),
          ),
          width: 190,
          height: 90,
          alignment: Alignment.topCenter,
          child: _buildMarker(
            icon: Icons.flight,
            color: Colors.deepPurple,
            label: '$label${code.isNotEmpty ? ' ($code)' : ''}',
          ),
        ),
      );
    }

    for (final place in widget.places) {
      if (place['latitude'] == null || place['longitude'] == null) {
        continue;
      }

      result.add(
        Marker(
          point: LatLng(
            (place['latitude'] as num).toDouble(),
            (place['longitude'] as num).toDouble(),
          ),
          width: 180,
          height: 90,
          alignment: Alignment.topCenter,
          child: _buildMarker(
            icon: Icons.location_on,
            color: Colors.blue,
            label: place['name']?.toString() ?? 'Place',
          ),
        ),
      );
    }

    return result;
  }

  Widget _buildMarker({
    required IconData icon,
    required Color color,
    required String label,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          constraints: const BoxConstraints(maxWidth: 170),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(8),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Text(
            label,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
          ),
        ),
        Icon(icon, size: 36, color: color),
      ],
    );
  }

  LatLng? get initialCenter {
    final hotel = widget.hotel;

    if (hotel != null &&
        hotel['latitude'] != null &&
        hotel['longitude'] != null) {
      return LatLng(
        (hotel['latitude'] as num).toDouble(),
        (hotel['longitude'] as num).toDouble(),
      );
    }

    for (final airport in widget.airports) {
      if (airport['latitude'] != null && airport['longitude'] != null) {
        return LatLng(
          (airport['latitude'] as num).toDouble(),
          (airport['longitude'] as num).toDouble(),
        );
      }
    }

    for (final place in widget.places) {
      if (place['latitude'] != null && place['longitude'] != null) {
        return LatLng(
          (place['latitude'] as num).toDouble(),
          (place['longitude'] as num).toDouble(),
        );
      }
    }

    return null;
  }

  void zoomIn() {
    final currentZoom = mapController.camera.zoom;

    mapController.move(mapController.camera.center, currentZoom + 1);
  }

  void zoomOut() {
    final currentZoom = mapController.camera.zoom;

    mapController.move(mapController.camera.center, currentZoom - 1);
  }

  @override
  Widget build(BuildContext context) {
    final center = initialCenter;
    final mapMarkers = markers;

    if (center == null || mapMarkers.isEmpty) {
      return const SizedBox.shrink();
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: SizedBox(
        height: 360,
        child: Stack(
          children: [
            FlutterMap(
              mapController: mapController,
              options: MapOptions(
                initialCenter: center,
                initialZoom: 12,
                minZoom: 3,
                maxZoom: 19,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.travel_ai_planner',
                ),
                MarkerLayer(markers: mapMarkers),
              ],
            ),

            Positioned(
              right: 12,
              bottom: 12,
              child: Column(
                children: [
                  _buildZoomButton(icon: Icons.add, onPressed: zoomIn),
                  const SizedBox(height: 4),
                  _buildZoomButton(icon: Icons.remove, onPressed: zoomOut),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildZoomButton({
    required IconData icon,
    required VoidCallback onPressed,
  }) {
    return Material(
      color: Colors.white,
      elevation: 3,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(8),
        child: SizedBox(width: 42, height: 42, child: Icon(icon, size: 24)),
      ),
    );
  }
}
