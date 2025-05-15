from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, g, send_file
from flask_login import login_required, current_user
from flask_socketio import emit
from . import data
from .forms import UploadDatasetForm, ShareDatasetForm
from ...models import db, Dataset, Share, User
from ...services.data_processor import DataProcessor
from ... import cache
import os

# Initialize the data processor service
data_processor = DataProcessor()

@data.route('/')
@login_required
def index():
    """Display the user's datasets."""
    # Get user's datasets
    user_datasets = Dataset.query.filter_by(user_id=current_user.id).order_by(Dataset.uploaded_at.desc()).all()
    
    # Get datasets shared with the user
    shared_datasets = db.session.query(Dataset).\
        select_from(Share).\
        join(Dataset, Share.object_id == Dataset.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'dataset'
        ).order_by(Dataset.uploaded_at.desc()).all()
    
    # Get public datasets (excluding user's own and already shared)
    user_dataset_ids = [ds.id for ds in user_datasets]
    shared_dataset_ids = [ds.id for ds in shared_datasets]
    public_datasets = Dataset.query.filter(
        Dataset.is_public == True,
        Dataset.user_id != current_user.id,
        ~Dataset.id.in_(shared_dataset_ids)
    ).order_by(Dataset.uploaded_at.desc()).all()
    
    return render_template(
        'data/index.html',
        title='My Datasets',
        user_datasets=user_datasets,
        shared_datasets=shared_datasets,
        public_datasets=public_datasets
    )

@data.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle dataset upload."""
    form = UploadDatasetForm()
    if form.validate_on_submit():
        try:
            # Process the uploaded file
            dataset = data_processor.process(
                form.file.data,
                current_user.id,
                form.is_public.data
            )
            
            flash('Dataset uploaded successfully!', 'success')
            return redirect(url_for('data.view', id=dataset.id))
        
        except Exception as e:
            flash(f'Error uploading dataset: {str(e)}', 'danger')
    
    return render_template('data/upload.html', title='Upload Dataset', form=form)

@data.route('/view/<int:id>')
@login_required
def view(id):
    """View a dataset."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            flash('You do not have permission to view this dataset.', 'danger')
            return redirect(url_for('data.index'))
    
    # Get dataset preview
    try:
        preview = data_processor.get_preview(dataset.id)
    except Exception as e:
        preview = f'<div class="alert alert-danger">Error loading preview: {str(e)}</div>'
    
    # Get visualisations for this dataset
    visualisations = dataset.visualisations.order_by(db.desc('created_at')).all()
    
    return render_template(
        'data/view.html',
        title=dataset.original_filename,
        dataset=dataset,
        preview=preview,
        visualisations=visualisations
    )

@data.route('/share/<int:id>', methods=['GET', 'POST'])
@login_required
def share(id):
    """Share a dataset with other users."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user owns this dataset
    if dataset.user_id != current_user.id:
        flash('You can only share datasets that you own.', 'danger')
        return redirect(url_for('data.index'))
    
    form = ShareDatasetForm()
    
    # Get all users except the current user for the form choices
    users = User.query.filter(User.id != current_user.id).all()
    form.user_id.choices = [(user.id, user.name) for user in users]
    
    if form.validate_on_submit():
        user_id = form.user_id.data
        
        # Check if the share already exists
        existing_share = Share.query.filter_by(
            owner_id=current_user.id,
            target_id=user_id,
            object_type='dataset',
            object_id=dataset.id
        ).first()
        
        if existing_share:
            flash('This dataset is already shared with this user.', 'warning')
        else:
            share = Share(
                owner_id=current_user.id,
                target_id=user_id,
                object_type='dataset',
                object_id=dataset.id
            )
            db.session.add(share)
            db.session.commit()
            flash('Dataset shared successfully!', 'success')
        
        return redirect(url_for('data.share', id=id))
    
    # Get all users this dataset is shared with
    shared_with = User.query.join(
    Share,  
    User.id == Share.target_id  
        ).filter(
    Share.owner_id == current_user.id,  
    Share.object_type == 'dataset',     
    Share.object_id == dataset.id       
        ).all()
    
    return render_template(
        'data/share.html',
        title=f'Share Dataset: {dataset.original_filename}',
        dataset=dataset,
        form=form,
        shared_with=shared_with
    )

@data.route('/unshare/<int:id>/<int:user_id>', methods=['POST'])
@login_required
def unshare(id, user_id):
    """Remove sharing access for a user."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user owns this dataset
    if dataset.user_id != current_user.id:
        flash('You can only manage sharing for datasets that you own.', 'danger')
        return redirect(url_for('data.index'))
    
    share = Share.query.filter_by(
        owner_id=current_user.id,
        target_id=user_id,
        object_type='dataset',
        object_id=dataset.id
    ).first_or_404()
    
    db.session.delete(share)
    db.session.commit()
    flash('Sharing access removed successfully!', 'success')
    
    return redirect(url_for('data.share', id=id))

@data.route('/toggle-public/<int:id>', methods=['POST'])
@login_required
def toggle_public(id):
    """Toggle the public status of a dataset."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user owns this dataset
    if dataset.user_id != current_user.id:
        flash('You can only change visibility for datasets that you own.', 'danger')
        return redirect(url_for('data.index'))
    
    dataset.is_public = not dataset.is_public
    db.session.commit()
    
    status = 'public' if dataset.is_public else 'private'
    flash(f'Dataset is now {status}.', 'success')
    
    return redirect(url_for('data.share', id=id))

@data.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a dataset."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user owns this dataset
    if dataset.user_id != current_user.id:
        flash('You can only delete datasets that you own.', 'danger')
        return redirect(url_for('data.index'))
    
    try:
        # Use the data processor to delete the dataset and its file
        data_processor.delete_dataset(dataset.id)
        flash('Dataset deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting dataset: {str(e)}', 'danger')
    
    return redirect(url_for('data.index'))

@data.route('/download/<int:id>')
@login_required
def download(id):
    """Download a dataset file."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            flash('You do not have permission to download this dataset.', 'danger')
            return redirect(url_for('data.index'))
    
    # Check if the file exists
    if not os.path.exists(dataset.file_path):
        flash('Dataset file not found.', 'danger')
        return redirect(url_for('data.view', id=dataset.id))
    
    return send_file(
        dataset.file_path,
        as_attachment=True,
        download_name=dataset.original_filename,
        mimetype='text/csv' if dataset.file_type == 'csv' else 'application/json'
    )

# API Routes

@data.route('/api/v1/datasets', methods=['GET'])
@login_required
@cache.cached(timeout=300)  # Cache this endpoint for 5 minutes
def api_get_datasets():
    """API endpoint to get all datasets for the current user."""
    datasets = Dataset.query.filter_by(user_id=current_user.id).order_by(Dataset.uploaded_at.desc()).all()
    
    result = []
    for ds in datasets:
        result.append({
            'id': ds.id,
            'filename': ds.original_filename,
            'file_type': ds.file_type,
            'n_rows': ds.n_rows,
            'n_columns': ds.n_columns,
            'is_public': ds.is_public,
            'uploaded_at': ds.uploaded_at.isoformat()
        })
    
    return jsonify(datasets=result)

@data.route('/api/v1/shared-datasets', methods=['GET'])
@login_required
@cache.cached(timeout=300)  # Cache this endpoint for 5 minutes
def api_get_shared_datasets():
    """API endpoint to get all datasets shared with the current user."""
    shared_datasets = db.session.query(Dataset).\
        select_from(Share).\
        join(Dataset, Share.object_id == Dataset.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'dataset'
        ).order_by(Dataset.uploaded_at.desc()).all()
    
    result = []
    for ds in shared_datasets:
        owner = User.query.get(ds.user_id)
        result.append({
            'id': ds.id,
            'filename': ds.original_filename,
            'file_type': ds.file_type,
            'n_rows': ds.n_rows,
            'n_columns': ds.n_columns,
            'is_public': ds.is_public,
            'uploaded_at': ds.uploaded_at.isoformat(),
            'owner': owner.name if owner else 'Unknown'
        })
    
    return jsonify(datasets=result)

@data.route('/api/v1/upload', methods=['POST'])
@login_required
def api_upload():
    """API endpoint for dataset upload."""
    if 'file' not in request.files:
        return jsonify(error='No file part'), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(error='No selected file'), 400
    
    is_public = request.form.get('is_public', 'false').lower() == 'true'
    
    try:
        # Process the uploaded file
        dataset = data_processor.process(
            file,
            current_user.id,
            is_public,
            current_user.id  # Use user ID as socket ID for progress updates
        )
        
        return jsonify(
            success=True,
            dataset_id=dataset.id,
            message='Dataset uploaded successfully!'
        )
    
    except Exception as e:
        return jsonify(error=f'Error uploading dataset: {str(e)}'), 500

@data.route('/api/v1/datasets/<int:id>', methods=['GET'])
@login_required
def api_get_dataset(id):
    """API endpoint to get a specific dataset."""
    dataset = Dataset.query.get_or_404(id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            return jsonify(error='You do not have permission to view this dataset.'), 403
    
    # Get dataset preview
    try:
        preview_html = data_processor.get_preview(dataset.id)
    except Exception as e:
        preview_html = f'<div class="alert alert-danger">Error loading preview: {str(e)}</div>'
    
    owner = User.query.get(dataset.user_id)
    
    return jsonify(
        id=dataset.id,
        filename=dataset.original_filename,
        file_type=dataset.file_type,
        n_rows=dataset.n_rows,
        n_columns=dataset.n_columns,
        is_public=dataset.is_public,
        uploaded_at=dataset.uploaded_at.isoformat(),
        owner=owner.name if owner else 'Unknown',
        preview_html=preview_html
    )