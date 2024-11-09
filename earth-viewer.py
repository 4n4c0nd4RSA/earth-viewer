import pyvista as pv
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import io

class EarthViewer:
    def __init__(self):
        # [Previous init code remains the same...]
        # Download Earth texture
        print("Downloading Earth texture...")
        texture_url = "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg"
        response = requests.get(texture_url)
        self.earth_texture = Image.open(BytesIO(response.content))
        self.texture_array = np.array(self.earth_texture)
        
        # Create sphere for Earth
        print("Creating Earth sphere...")
        self.sphere = pv.Sphere(radius=1, phi_resolution=100, theta_resolution=200)
        
        # Create texture coordinates
        print("Creating texture coordinates...")
        x, y, z = self.sphere.points.T
        r = np.sqrt(x**2 + y**2 + z**2)
        theta = np.arctan2(y, x)
        phi = np.arccos(z/r)
        
        u = (theta + np.pi) / (2*np.pi)
        v = 1 - (phi / np.pi)
        
        texture_coords = np.column_stack((u, v))
        self.sphere.active_texture_coordinates = texture_coords
        
        # Set up the plotter
        print("Setting up visualization...")
        self.plotter = pv.Plotter()
        self.plotter.background_color = 'black'
        
        # Add the textured sphere
        self.plotter.add_mesh(
            self.sphere,
            texture=self.texture_array,
            smooth_shading=True,
            show_edges=False,
        )
        
        # Set up camera
        self.plotter.camera_position = 'xz'
        self.plotter.enable_point_picking(callback=self.point_clicked, show_message=False)
        
        print("Setup complete!")

    def create_map_projection(self, center_lat, center_lon):
        """Create appropriate map projection based on clicked location"""
        fig = plt.figure(figsize=(20, 10))
        
        # First subplot: Orthographic view (unchanged)
        ax1 = plt.subplot(121, projection=ccrs.Orthographic(center_lon, center_lat))
        ax1.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax1.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax1.add_feature(cfeature.LAND, color='lightgray')
        ax1.add_feature(cfeature.OCEAN, color='lightblue')
        ax1.stock_img()
        ax1.gridlines(color='gray', alpha=0.5, linestyle='--')
        ax1.plot([center_lon], [center_lat], 'ro', transform=ccrs.PlateCarree(), 
                markersize=10, label='Selected Point')
        ax1.set_title(f'Orthographic View\nCentered at {center_lat:.1f}°N, {center_lon:.1f}°E')
        
        # Second subplot: Create rotated Lambert Cylindrical projection
        # Create a rotated geodetic coordinate system
        rotated_pole = ccrs.RotatedPole(
            pole_longitude=center_lon + 180,
            pole_latitude=-center_lat,
            central_rotated_longitude=0
        )
        
        # Use this as the base for our Lambert Cylindrical
        ax2 = plt.subplot(122, projection=rotated_pole)
        
        # Add map features with explicit transform
        ax2.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax2.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax2.add_feature(cfeature.LAND, color='lightgray')
        ax2.add_feature(cfeature.OCEAN, color='lightblue')
        ax2.stock_img()
        
        # Add gridlines with labels
        gl = ax2.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                          linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        
        # Set the extent in the rotated coordinate system
        ax2.set_global()
        
        # Transform the center point to the rotated system and plot it
        ax2.plot([center_lon], [center_lat], 'ro', transform=ccrs.PlateCarree(),
                markersize=10, label='Selected Point')
        
        # Set title
        ax2.set_title(f'Rotated Lambert Cylindrical Projection\nCentered at {center_lat:.1f}°N, {center_lon:.1f}°E')
        
        # Add legends
        ax1.legend(loc='lower left')
        ax2.legend(loc='lower left')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='black')
        buf.seek(0)
        plt.close()
        
        # Show the map
        img = Image.open(buf)
        img.show()
        
    def show(self):
        """Display the interactive globe"""
        print("\nEarth Viewer Ready!")
        print("Click anywhere on the globe to see two views:")
        print("1. Orthographic projection centered on clicked point")
        print("2. Cylindrical projection centered on clicked longitude")
        print("Close the window to exit.")
        self.plotter.show()

    def cartesian_to_spherical(self, x, y, z):
        """Convert Cartesian coordinates to spherical (lat/lon)"""
        r = np.sqrt(x**2 + y**2 + z**2)
        lat = np.arcsin(z/r) * 180/np.pi
        lon = np.arctan2(y, x) * 180/np.pi
        return lat, lon

    def point_clicked(self, point):
        """Handle click events on the globe"""
        try:
            x, y, z = point
            lat, lon = self.cartesian_to_spherical(x, y, z)
            print(f"Clicked at latitude: {lat:.2f}°, longitude: {lon:.2f}°")
            
            # Create projection
            self.create_map_projection(lat, lon)
            
        except Exception as e:
            print(f"Error handling click: {str(e)}")

if __name__ == "__main__":
    print("Initializing Earth Viewer...")
    try:
        viewer = EarthViewer()
        viewer.show()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all required packages are installed:")
        print("   pip install -r requirements.txt")
        print("2. Try updating PyVista:")
        print("   pip install --upgrade pyvista")
        print("3. Check if your graphics drivers are up to date")