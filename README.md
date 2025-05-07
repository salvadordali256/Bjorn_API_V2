# Bjorn_API_V2# Bjorn HVAC Abbreviation Tool

The Bjorn HVAC Abbreviation Tool is an intelligent system that automatically abbreviates HVAC (Heating, Ventilation, and Air Conditioning) part descriptions to fit within a specified character limit, typically 30 characters.

## Features

- **Machine Learning-Based Abbreviation**: Uses trained models to intelligently abbreviate HVAC terminology
- **Hybrid Approach**: Combines domain-specific knowledge with ML for optimal results
- **Web Interface**: User-friendly drag-and-drop interface for CSV processing
- **API Access**: Direct API endpoints for integration with other systems
- **Performance Statistics**: Detailed metrics on abbreviation performance

## Technical Architecture

- **Python Flask Backend**: Handles API requests and web interface
- **Machine Learning Models**: Two model types (basic and hybrid)
- **MySQL Database**: Stores abbreviation patterns and usage statistics
- **Docker Deployment**: Containerized for easy deployment

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/Bjorn_API_v2_Final.git
cd Bjorn_API_v2_Final
```

2. Start the containers
```bash
docker-compose up -d
```

3. Access the web interface at http://localhost:8000

### Using the API

The Bjorn HVAC Abbreviation Tool provides several API endpoints:

- `/api/abbreviate` - Abbreviate text or process CSV files
- `/api/ml/status` - Check ML model status
- `/api/dictionary` - Get or update the abbreviation dictionary
- `/api/config` - Get or update configuration
- `/api/stats` - Get abbreviation statistics

Example usage:

```bash
# Abbreviate a single text
curl -X POST http://localhost:8000/api/abbreviate \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'text=heating ventilation and air conditioning system with temperature control'

# Process a CSV file
curl -X POST http://localhost:8000/api/abbreviate \
  -F "file=@/path/to/file.csv" \
  -F "use_ml=true" \
  -F "target_length=30"
```

## CSV File Format

The input CSV file should contain at least these columns:
- Part Number
- Part Definition

The output will include additional columns:
- Abbreviation
- Original Length
- Final Length
- Length Reduction
- Applied Rules
- Method Used
- And more

## License

[Your License Information]

## Acknowledgments

- HVAC industry standards
- Contributors and beta testers