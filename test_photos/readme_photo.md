# Photo Organizer

An intelligent, privacy-first photo organization tool that uses AI to help you manage your photo collection.

## Features

### 🎯 Face Recognition & Filtering
- **Automatic Face Detection**: Detects and clusters faces in your photos using DeepFace
- **Person Tagging**: Assign names to face groups and build a person database
- **Smart Search**: Filter photos by specific people with confidence scoring
- **Batch Operations**: Copy/move photos containing selected individuals

### 🤖 Content Intelligence
- **Irrelevant Content Detection**: Automatically identifies memes, screenshots, and text messages
- **Smart Classification**: Uses AI to distinguish between personal photos and digital clutter
- **Review Workflow**: Pause/resume photo review session at your own pace
- **Automated Organization**: Move confirmed irrelevant photos to separate folders

### 🔒 Privacy-First Design
- **Local Processing**: All ML processing happens on your local machine
- **No Cloud Dependencies**: Your photos never leave your device
- **Data Control**: Complete control over your photo data and metadata
- **Transparent Operations**: Clear logging of all processing activities

### 🌐 Cross-Platform Web Interface
- **Modern Web UI**: Responsive design works on desktop, tablet, and mobile
- **Real-time Progress**: Live updates during photo processing
- **Keyboard Shortcuts**: Power-user shortcuts for efficient navigation
- **Dark/Light Themes**: Comfortable viewing for extended sessions

## Quick Start

### Prerequisites

- Python 3.12+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- For GPU acceleration: NVIDIA GPU with CUDA support (optional)

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd photo-organiser
```

2. **Install Dependencies**
```bash
# Using UV (recommended)
pip install uv
uv sync --dev

# Or with pip
python -m venv photo_env
source photo_env/bin/activate  # On Windows: photo_env\Scripts\activate
pip install -e .
```

3. **Initialize Database**
```bash
uv run python -m photo_organiser init-db
```

4. **Start the Application**
```bash
# Start backend server
uv run python -m photo_organiser serve

# In another terminal, start frontend (if developing locally)
cd frontend
npm install
npm start
```

5. **Access the Application**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Web Interface: http://localhost:3000 (when running frontend locally)

## Usage

### 1. Add Your Photo Collection
1. Open the web interface
2. Click "Add Photo Folder" and select a directory containing photos
3. Wait for initial processing to complete
4. Review detected faces and content classifications

### 2. Organize by People
1. Go to the "Faces" tab
2. Click on face groups and assign names to people
3. Use the "Photos" tab to filter by specific people
4. Export filtered photos to organized folders

### 3. Clean Up Irrelevant Content
1. Go to the "Review" tab
2. Start reviewing photos flagged as potentially irrelevant
3. Make decisions: Keep, Remove, or Maybe
4. Use "Move Irrelevant" to automatically organize confirmed items

## Architecture

### Backend (FastAPI + Python)
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: Database ORM with SQLite for simplicity
- **ChromaDB**: Vector database for face embeddings
- **DeepFace**: Face detection and recognition
- **EasyOCR**: Text extraction from images
- **OpenCV**: Computer vision operations
- **PyTorch**: ML model backend

### Frontend (React + TypeScript)
- **React 18**: Modern component-based UI
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Zustand**: Lightweight state management
- **React Query**: Server state management

### ML/AI Processing
- **Face Detection**: RetinaFace + FaceNet512 for high accuracy
- **Face Clustering**: Cosine similarity on face embeddings
- **Content Classification**: Custom models for meme/screenshot detection
- **Text Extraction**: OCR for identifying text-heavy images

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./photo_organizer.db
CHROMA_DB_PATH=./chroma_db

# Processing
MAX_BATCH_SIZE=32
MAX_WORKERS=4
MEMORY_THRESHOLD_GB=8

# File Storage
PHOTO_ROOT_DIR=./photos
THUMBNAIL_DIR=./thumbnails
EXPORT_DIR=./exports

# Optional: GPU acceleration
CUDA_VISIBLE_DEVICES=0
```

### Development Settings
```bash
# Enable debug mode
DEBUG=true

# Enable GPU if available
USE_GPU=true

# Log level
LOG_LEVEL=INFO
```

## Performance

### Recommended Hardware
- **Minimum**: 8GB RAM, 4+ CPU cores
- **Recommended**: 16GB+ RAM, 8+ CPU cores, NVIDIA GPU with 6GB+ VRAM
- **Storage**: SSD recommended for large photo collections

### Performance Benchmarks
- **Face Detection**: ~2 seconds per photo (CPU), ~0.5 seconds (GPU)
- **Content Classification**: ~3 seconds per photo (CPU), ~1 second (GPU)
- **Batch Processing**: ~100 photos/minute (CPU), ~300 photos/minute (GPU)

### Scaling Considerations
- **10K photos**: ~30-60 minutes initial processing
- **50K photos**: ~2-4 hours initial processing
- **100K+ photos**: Consider batch processing overnight

## Development

### Project Structure
```
photo-organiser/
├── src/photo_organiser/           # Main package
│   ├── core/                      # Core business logic
│   ├── models/                    # Database models
│   ├── services/                  # Business services
│   ├── api/                       # FastAPI endpoints
│   ├── utils/                     # Utility functions
│   └── config/                    # Configuration management
├── frontend/                      # React frontend
├── tests/                         # Test suites
├── docs/                          # Documentation
└── pyproject.toml                 # Project configuration
```

### Development Commands
```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy .

# Testing
uv run pytest
uv run pytest tests/test_specific.py::test_function

# Database migrations
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head

# Build for distribution
uv build
```

### Code Quality
- **Type Hints**: Full type annotation coverage
- **Documentation**: Comprehensive docstrings for all public functions
- **Testing**: Unit tests for core logic, integration tests for workflows
- **Linting**: Ruff for code quality, Black for formatting
- **Security**: Input validation, SQL injection prevention, file system safety

## Privacy & Security

### Data Protection
- **Local-First**: All processing happens on your local machine
- **No Uploads**: Photos are never sent to external services
- **Metadata Protection**: Original photo metadata is preserved and never transmitted
- **Transparent Processing**: All operations are logged and auditable

### File System Access
- **Sandboxed**: App only accesses directories you explicitly authorize
- **Safe Operations**: All file operations include validation and error handling
- **Backup Protection**: Original files are never modified without explicit consent
- **Undo Support**: Most operations support undo for user errors

## Troubleshooting

### Common Issues

#### "Out of Memory" Errors
```bash
# Reduce batch size in config
MAX_BATCH_SIZE=16
MEMORY_THRESHOLD_GB=6
```

#### "Face Detection Failed"
```bash
# Try different face detection backends
export FACE_DETECTOR_BACKEND=opencv
export FACE_MODEL_NAME=VGG-Face
```

#### "Slow Processing"
```bash
# Enable GPU if available
export USE_GPU=true
export TORCH_CUDA_ARCH_LIST="6.0;7.0;8.0"
```

### Logs and Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View processing logs
tail -f logs/photo_organiser.log

# Database inspection
uv run python -m photo_organiser db-inspect
```

## Contributing

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with comprehensive tests
4. **Run quality checks**: `uv run ruff check . && uv run mypy . && uv run pytest`
5. **Commit** your changes: `git commit -m 'Add amazing feature'`
6. **Push** to the branch: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new functionality
- Update documentation for API changes
- Use type hints throughout
- Keep commits focused and atomic

## Roadmap

### Version 0.1.0 (Current)
- ✅ Basic face detection and clustering
- ✅ Simple content classification
- ✅ Web interface for review and organization
- ✅ Local-only processing

### Version 0.2.0 (Planned)
- 🔄 Enhanced face recognition accuracy
- 🔄 Advanced content filtering (memes, screenshots, documents)
- 🔄 Batch processing optimization
- 🔄 Mobile-responsive design improvements

### Version 0.3.0 (Future)
- 📋 Video content analysis
- 📋 Advanced search by metadata
- 📋 Integration with cloud storage (optional)
- 📋 Multi-user support (family sharing)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [DeepFace](https://github.com/serengil/deepface) for face recognition capabilities
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for text extraction
- [ChromaDB](https://github.com/chroma-core/chroma) for vector similarity search
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework

## Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing [GitHub Issues](https://github.com/your-repo/issues)
3. Create a new issue with detailed information about your problem
4. Include system information and error logs when possible

---

**Photo Organizer** - Take control of your digital memories with privacy-first AI.