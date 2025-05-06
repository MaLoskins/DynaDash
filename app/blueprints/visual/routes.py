from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
from flask_socketio import emit
from markupsafe import Markup
from . import visual
from ...models import db, Dataset, Visualisation, Share, User
from .forms import GenerateVisualisationForm, ShareVisualisationForm
from ...services.claude_client import ClaudeClient
from ... import cache

# Initialize the Claude client service
claude_client = ClaudeClient()

@visual.route('/welcome')
def welcome():
    return render_template('visual/welcome.html', title='Welcome')

@visual.route('/index')
@login_required
def index():
    """Display the visualizations gallery."""
    # Get user's visualizations
    user_visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    # Get visualizations shared with the user
    shared_visualisations = db.session.query(Visualisation).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc()).all()
    
    return render_template(
        'visual/index.html',
        title='My Visualizations',
        user_visualisations=user_visualisations,
        shared_visualisations=shared_visualisations
    )

@visual.route('/generate/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def generate(dataset_id):
    """Generate visualizations for a dataset."""
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            flash('You do not have permission to visualize this dataset.', 'danger')
            return redirect(url_for('data.index'))
    
    form = GenerateVisualisationForm()
    if form.validate_on_submit():
        # Start the visualization generation process
        try:
            # Emit a socket event to start the progress bar
            from ... import socketio
            socketio.emit('progress_update', {'percent': 0, 'message': 'Starting visualization generation...'}, room=current_user.id)
            
            # Generate the visualization using Claude
            visualization_html = claude_client.generate_visualization(dataset.id, form.chart_type.data, form.title.data)
            
            # Create a new visualization record
            visualisation = Visualisation(
                dataset_id=dataset.id,
                title=form.title.data,
                description=form.description.data,
                spec=visualization_html
            )
            db.session.add(visualisation)
            db.session.commit()
            
            # Emit a socket event to complete the progress bar
            socketio.emit('processing_complete', room=current_user.id)
            
            flash('Visualization generated successfully!', 'success')
            return redirect(url_for('visual.view', id=visualisation.id))
        
        except Exception as e:
            flash(f'Error generating visualization: {str(e)}', 'danger')
    
    return render_template(
        'visual/generate.html',
        title='Generate Visualization',
        dataset=dataset,
        form=form
    )

@visual.route('/view/<int:id>')
@login_required
def view(id):
    """View a visualization."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user has access to this visualization
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the visualization is shared with the user
        share = Share.query.filter_by(
            object_type='visualisation',
            object_id=visualisation.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            flash('You do not have permission to view this visualization.', 'danger')
            return redirect(url_for('visual.index'))
    # Ensure the visualization spec is properly marked as safe HTML
    vis_html = Markup(visualisation.spec)
    
    return render_template(
        'visual/view.html',
        title=visualisation.title,
        visualisation=visualisation,
        vis_html=vis_html,
        dataset=dataset
    )

@visual.route('/share/<int:id>', methods=['GET', 'POST'])
@login_required
def share(id):
    """Share a visualization with other users."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user owns this visualization
    if dataset.user_id != current_user.id:
        flash('You can only share visualizations that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    form = ShareVisualisationForm()
    
    # Get all users except the current user for the form choices
    users = User.query.filter(User.id != current_user.id).all()
    form.user_id.choices = [(user.id, user.name) for user in users]
    
    if form.validate_on_submit():
        user_id = form.user_id.data
        
        # Check if the share already exists
        existing_share = Share.query.filter_by(
            owner_id=current_user.id,
            target_id=user_id,
            object_type='visualisation',
            object_id=visualisation.id
        ).first()
        
        if existing_share:
            flash('This visualization is already shared with this user.', 'warning')
        else:
            share = Share(
                owner_id=current_user.id,
                target_id=user_id,
                object_type='visualisation',
                object_id=visualisation.id
            )
            db.session.add(share)
            db.session.commit()
            flash('Visualization shared successfully!', 'success')
        
        return redirect(url_for('visual.share', id=id))
    
    # Get all users this visualization is shared with
    shared_with = User.query.join(Share).filter(
        Share.owner_id == current_user.id,
        Share.object_type == 'visualisation',
        Share.object_id == visualisation.id
    ).all()
    
    return render_template(
        'visual/share.html',
        title=f'Share Visualization: {visualisation.title}',
        visualisation=visualisation,
        form=form,
        shared_with=shared_with
    )

@visual.route('/unshare/<int:id>/<int:user_id>', methods=['POST'])
@login_required
def unshare(id, user_id):
    """Remove sharing access for a user."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user owns this visualization
    if dataset.user_id != current_user.id:
        flash('You can only manage sharing for visualizations that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    share = Share.query.filter_by(
        owner_id=current_user.id,
        target_id=user_id,
        object_type='visualisation',
        object_id=visualisation.id
    ).first_or_404()
    
    db.session.delete(share)
    db.session.commit()
    flash('Sharing access removed successfully!', 'success')
    
    return redirect(url_for('visual.share', id=id))

@visual.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a visualization."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user owns this visualization
    if dataset.user_id != current_user.id:
        flash('You can only delete visualizations that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    # Delete all shares for this visualization
    Share.query.filter_by(object_type='visualisation', object_id=visualisation.id).delete()
    
    # Delete the visualization record
    db.session.delete(visualisation)
    db.session.commit()
    
    flash('Visualization deleted successfully!', 'success')
    return redirect(url_for('visual.index'))

# API Routes

@visual.route('/api/v1/visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=300)  # Cache for 5 minutes
def api_get_visualisations():
    """API endpoint to get all visualizations for the current user."""
    visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    result = []
    for vis in visualisations:
        dataset = Dataset.query.get(vis.dataset_id)
        result.append({
            'id': vis.id,
            'title': vis.title,
            'description': vis.description,
            'dataset_name': dataset.original_filename,
            'created_at': vis.created_at.isoformat()
        })
    
    return jsonify(visualisations=result)

@visual.route('/api/v1/shared-visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=300)  # Cache for 5 minutes
def api_get_shared_visualisations():
    """API endpoint to get all visualizations shared with the current user."""
    shared_visualisations = db.session.query(Visualisation).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc()).all()
    
    result = []
    for vis in shared_visualisations:
        dataset = Dataset.query.get(vis.dataset_id)
        owner = User.query.get(dataset.user_id)
        result.append({
            'id': vis.id,
            'title': vis.title,
            'description': vis.description,
            'dataset_name': dataset.original_filename,
            'created_at': vis.created_at.isoformat(),
            'owner': owner.name if owner else 'Unknown'
        })
    
    return jsonify(visualisations=result)

@visual.route('/api/v1/generate', methods=['POST'])
@login_required
def api_generate():
    """API endpoint for visualization generation."""
    data = request.get_json()
    if not data:
        return jsonify(error='No data provided'), 400
    
    dataset_id = data.get('dataset_id')
    chart_type = data.get('chart_type')
    title = data.get('title')
    description = data.get('description', '')
    
    if not dataset_id or not chart_type or not title:
        return jsonify(error='Dataset ID, chart type, and title are required'), 400
    
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            return jsonify(error='You do not have permission to visualize this dataset.'), 403
    
    try:
        # Generate the visualization using Claude
        visualization_html = claude_client.generate_visualization(dataset_id, chart_type, title)
        
        # Create a new visualization record
        visualisation = Visualisation(
            dataset_id=dataset_id,
            title=title,
            description=description,
            spec=visualization_html
        )
        db.session.add(visualisation)
        db.session.commit()
        
        return jsonify(
            success=True,
            visualisation_id=visualisation.id,
            message='Visualization generated successfully!'
        )
    
    except Exception as e:
        return jsonify(error=f'Error generating visualization: {str(e)}'), 500

@visual.route('/api/v1/visualisations/<int:id>', methods=['GET'])
@login_required
@cache.cached(timeout=120)  # Cache for 2 minutes
def api_get_visualisation(id):
    """API endpoint to get a specific visualization."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user has access to this visualization
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the visualization is shared with the user
        share = Share.query.filter_by(
            object_type='visualisation',
            object_id=visualisation.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            return jsonify(error='You do not have permission to view this visualization.'), 403
    
    return jsonify(
        id=visualisation.id,
        title=visualisation.title,
        description=visualisation.description,
        spec=visualisation.spec,
        dataset_id=visualisation.dataset_id,
        created_at=visualisation.created_at.isoformat()
    )