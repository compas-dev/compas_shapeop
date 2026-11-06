#include "compas.h"

//╔═══════════════════════════════════════════════════════════════════════════╗
//║                        DYNAMIC and STATIC SOLVER CLASS                    ║
//╚═══════════════════════════════════════════════════════════════════════════╝

/**
 * @brief Wrapper class for ShapeOp::Solver with dynamic memory management
 * @details Provides a C++ interface between ShapeOp library and Python with
 *          automatic memory management using std::unique_ptr
 */
class SolverWrapper {
private:
    std::unique_ptr<ShapeOp::Solver> solver;  //!< Managed ShapeOp solver instance
    
    /**
     * @brief Helper method to check if solver is valid
     * @return true if solver pointer is not null
     */
    bool is_valid() const {
        return solver != nullptr;
    }
    
public:
    /**
     * @brief Constructor for the SolverWrapper
     * @throws std::runtime_error if solver creation fails
     */
    SolverWrapper() : 
        solver(std::make_unique<ShapeOp::Solver>()) {
        if (!solver) {
            throw std::runtime_error("Failed to create ShapeOp solver");
        }
    }
    
    /**
     * @brief Destructor for the SolverWrapper
     * @details The unique_ptr will automatically release the solver
     */
    ~SolverWrapper() {
        // The unique_ptr will automatically release the solver
    }
    
    //┌───────────────────────────────────────────────────────────────────────┐
    //│                    SOLVER CORE FUNCTIONALITY                          │
    //└───────────────────────────────────────────────────────────────────────┘
    
    /**
     * @brief Get a reference to the solver's internal points matrix
     * @details Provides zero-copy access to the solver's internal points
     * @return Reference to the solver's points matrix
     * @throws std::runtime_error if solver is invalid
     */
    Eigen::Ref<Eigen::MatrixXd> get_points() {
        if (!is_valid()) {
            throw std::runtime_error("Invalid solver");
        }
        // Direct access to the solver's points matrix
        return solver->points_;
    }
    
    /**
    * @brief Set the solver's internal points matrix directly from a NumPy array
    * @details Provides zero-copy transfer from a NumPy array to the solver's internal points
    * @param points_array NumPy array of shape (3, n) in F-order
    * @throws std::runtime_error if solver is invalid or array has incorrect dimensions
    */
    void set_points(nb::ndarray<double> points_array) {
        if (!is_valid()) {
            throw std::runtime_error("Invalid solver");
        }
        
        // Check dimensions - nanobind requires index for shape
        if (points_array.ndim() != 2 || points_array.shape(0) != 3) {
            throw std::runtime_error("Points array must have shape (3, n)");
        }
        
        size_t num_points = points_array.shape(1);
        if (num_points == 0) {
            throw std::runtime_error("Empty points array");
        }
        
        // Get data pointer
        double* data = const_cast<double*>(points_array.data());
        
        // Check if array is F-contiguous (column-major) with correct strides
        if (points_array.stride(0) == 1 && points_array.stride(1) == 3) {
            // We copy here
            solver->points_ = Eigen::Map<ShapeOp::Matrix3X>(data, 3, num_points);
        } else {
            // If not F-contiguous, we need a conversion step
            throw std::runtime_error("Points array must be in Fortran order (column-major)");
        }
    }
    
    /**
     * @brief Initialize the solver
     * @param dynamic Whether to use dynamic simulation (default: false)
     * @param masses Mass value for dynamic simulation (default: 1.0)
     * @param damping Damping factor for dynamic simulation (default: 1.0)
     * @param timestep Time step for dynamic simulation (default: 1.0)
     * @return true if initialization is successful
     */
    bool initialize(bool dynamic = false, double masses = 1.0, double damping = 1.0, double timestep = 1.0) {
        if (!is_valid()) {
            return false;
        }
        
        // Pass parameters directly to the solver
        return solver->initialize(dynamic, masses, damping, timestep);
    }
    
    /**
     * @brief Solve for a number of iterations
     * @param iterations Number of iterations to solve for
     * @return true if solve is successful
     */
    bool solve(int iterations) {
        if (!is_valid()) {
            return false;
        }
        
        return solver->solve(iterations);
    }
    
    //┌───────────────────────────────────────────────────────────────────────┐
    //│                    GEOMETRIC CONSTRAINTS                              │
    //└───────────────────────────────────────────────────────────────────────┘
    
    /**
     * @brief Add closeness constraint
     * @param vertex_index Vertex index
     * @param weight Weight of the constraint
     * @return true if constraint is added successfully
     */
    bool add_closeness_constraint(int vertex_index, double weight) {
        if (!is_valid()) {
            return false;
        }
        
        std::vector<int> indices_vec = {vertex_index};
        
        auto constraint = std::make_shared<ShapeOp::ClosenessConstraint>(
            indices_vec, weight, solver->getPoints());
        
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add closeness constraint with target position
     * @param vertex_index Vertex index
     * @param weight Weight of the constraint
     * @param x X-coordinate of the target position
     * @param y Y-coordinate of the target position
     * @param z Z-coordinate of the target position
     * @return true if constraint is added successfully
     */
    bool add_closeness_constraint_with_position(int vertex_index, double weight, double x, double y, double z) {
        if (!is_valid()) {
            return false;
        }
        
        // Create indices vector (ShapeOp requires vector but only uses one index)
        std::vector<int> indices_vec = {vertex_index};
        
        // Create the constraint
        auto constraint = std::make_shared<ShapeOp::ClosenessConstraint>(
            indices_vec, weight, solver->getPoints());
        
        // Create and set the target position
        ShapeOp::Vector3 pos;
        pos(0) = x;
        pos(1) = y;
        pos(2) = z;
        
        // Set the target position
        constraint->setPosition(pos);
        
        // Add constraint to solver
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add edge strain constraint
     * @param vertex_index1 First vertex index
     * @param vertex_index2 Second vertex index
     * @param weight Weight of the constraint
     * @param min_range Minimum range of the constraint
     * @param max_range Maximum range of the constraint
     * @return true if constraint is added successfully
     */
    bool add_edge_strain_constraint(int vertex_index1, int vertex_index2, double weight, double min_range, double max_range) {
        if (!is_valid()) {
            return false;
        }
        
        std::vector<int> indices_vec = {vertex_index1, vertex_index2};
        
        auto constraint = std::make_shared<ShapeOp::EdgeStrainConstraint>(
            indices_vec, weight, solver->getPoints(), min_range, max_range);
        
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add shrinking edge constraint (specifically for cable nets)
     * @param vertex_index1 First vertex index
     * @param vertex_index2 Second vertex index
     * @param weight Weight of the constraint
     * @param shrink_factor Target edge length as a ratio of the original length
     * @return true if constraint is added successfully
     */
    bool add_shrinking_edge_constraint(int vertex_index1, int vertex_index2, double weight, double shrink_factor) {
        if (!is_valid()) {
            return false;
        }
        
        std::vector<int> indices_vec = {vertex_index1, vertex_index2};
        
        // Calculate the min/max range based on the shrink factor
        double min_range = shrink_factor - 0.05;  // 5% below target
        double max_range = shrink_factor + 0.05;  // 5% above target
        
        auto constraint = std::make_shared<ShapeOp::EdgeStrainConstraint>(
            indices_vec, weight, solver->getPoints(), min_range, max_range);
        
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add circle constraint (for face circularization)
     * @param indices Vector of vertex indices
     * @param weight Weight of the constraint
     * @return true if constraint is added successfully
     */
    bool add_circle_constraint(std::vector<int> indices, double weight) {
        if (!is_valid()) {
            return false;
        }
        
        // Circle constraint requires at least 3 vertices
        if (indices.size() < 3) {
            throw std::runtime_error("Circle constraint requires at least 3 vertices");
        }
        
        auto constraint = std::make_shared<ShapeOp::CircleConstraint>(
            indices, weight, solver->getPoints());
        
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add plane constraint (for face planarization)
     * @param indices Vector of vertex indices
     * @param weight Weight of the constraint
     * @return true if constraint is added successfully
     */
    bool add_plane_constraint(std::vector<int> indices, double weight) {
        if (!is_valid()) {
            return false;
        }

        // Validate that we have at least 3 vertices (needed for a plane)
        if (indices.size() < 3) {
            throw std::runtime_error("Plane constraint requires at least 3 vertices");
        }

        // Create the constraint
        auto constraint = std::make_shared<ShapeOp::PlaneConstraint>(indices, weight, solver->getPoints());
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add similarity constraint (for regular polygon formation)
     * @param indices Vector of vertex indices
     * @param weight Weight of the constraint
     * @param allow_scaling Whether to allow scaling transformations
     * @param allow_rotation Whether to allow rotation transformations
     * @param allow_translation Whether to allow translation transformations
     * @return true if constraint is added successfully
     */
    bool add_similarity_constraint(std::vector<int> indices, double weight, 
                                  bool allow_scaling, bool allow_rotation, bool allow_translation) {
        if (!is_valid()) {
            return false;
        }
        
        // Create the constraint
        auto constraint = std::make_shared<ShapeOp::SimilarityConstraint>(
            indices, weight, solver->getPoints(), 
            allow_scaling, allow_rotation, allow_translation);
        
        return solver->addConstraint(constraint) >= 0;
    }
    
    /**
     * @brief Add regular polygon constraint for a face (high-level convenience function)
     * @param indices Vector of vertex indices
     * @param weight Weight of the constraint
     * @return true if constraint is added successfully
     */
    bool add_regular_polygon_constraint(std::vector<int> indices, double weight) {
        if (!is_valid()) {
            return false;
        }
        
        // Need at least 3 vertices to define a polygon
        if (indices.size() < 3) {
            throw std::runtime_error("Regular polygon constraint requires at least 3 vertices");
        }
        
        // Calculate face centroid
        ShapeOp::Vector3 centroid = ShapeOp::Vector3::Zero();
        for (const auto& id : indices) {
            centroid += solver->getPoints().col(id);
        }
        centroid /= indices.size();
        
        // Calculate face normal using first three points
        ShapeOp::Vector3 p0 = solver->getPoints().col(indices[0]);
        ShapeOp::Vector3 p1 = solver->getPoints().col(indices[1]);
        ShapeOp::Vector3 p2 = solver->getPoints().col(indices[2]);
        ShapeOp::Vector3 normal = (p1 - p0).cross(p2 - p0).normalized();
        
        // Create a local coordinate system on the face
        ShapeOp::Vector3 x_axis = ShapeOp::Vector3(1, 0, 0);
        if (std::abs(x_axis.dot(normal)) > 0.9) {
            x_axis = ShapeOp::Vector3(0, 1, 0);
        }
        x_axis = (x_axis - normal * x_axis.dot(normal)).normalized();
        ShapeOp::Vector3 y_axis = normal.cross(x_axis).normalized();
        
        // Create a regular polygon template
        ShapeOp::Matrix3X shape(3, indices.size());
        for (size_t i = 0; i < indices.size(); i++) {
            double angle = 2.0 * M_PI * i / indices.size();
            ShapeOp::Vector3 pt = centroid + 
                                  x_axis * std::cos(angle) + 
                                  y_axis * std::sin(angle);
            shape.col(i) = pt;
        }
        
        // Create a similarity constraint
        auto constraint = std::make_shared<ShapeOp::SimilarityConstraint>(
            indices, weight, solver->getPoints(), true, true, true);
        
        // Set the regular polygon shape
        std::vector<ShapeOp::Matrix3X> shapes;
        shapes.push_back(shape);
        constraint->setShapes(shapes);
        
        return solver->addConstraint(constraint) >= 0;
    }

    /**
     * @brief Add a regular-polygon, similarity, or custom shape constraint
     * @param indices Vector of vertex indices
     * @param shape_type One of regular_polygon, similarity, or custom
     * @param weight Weight of the constraint
     * @param allow_scaling Whether the shape may scale
     * @param allow_rotation Whether cyclic vertex rotations are considered
     * @param allow_translation Whether flipped vertex order is considered
     * @param custom_points Custom target points for a custom shape
     * @return true if the constraint is added successfully
     */
    bool add_shape_constraint(std::vector<int> indices,
                              const std::string& shape_type,
                              double weight,
                              bool allow_scaling,
                              bool allow_rotation,
                              bool allow_translation,
                              const std::vector<std::vector<double>>& custom_points) {
        if (!is_valid()) {
            return false;
        }

        if (shape_type == "regular_polygon") {
            return add_regular_polygon_constraint(indices, weight);
        }
        if (shape_type != "similarity" && shape_type != "custom") {
            throw std::runtime_error("Shape type must be 'regular_polygon', 'similarity', or 'custom'");
        }
        if (indices.size() < 2) {
            throw std::runtime_error("Shape constraints require at least 2 vertices");
        }

        auto constraint = std::make_shared<ShapeOp::SimilarityConstraint>(
            indices, weight, solver->getPoints(), allow_scaling, allow_rotation, allow_translation);

        if (shape_type == "custom") {
            if (custom_points.size() != indices.size()) {
                throw std::runtime_error("Custom shape point count must match the vertex index count");
            }

            ShapeOp::Matrix3X shape(3, custom_points.size());
            for (size_t i = 0; i < custom_points.size(); ++i) {
                if (custom_points[i].size() != 3) {
                    throw std::runtime_error("Custom shape points must have exactly 3 coordinates");
                }
                shape(0, i) = custom_points[i][0];
                shape(1, i) = custom_points[i][1];
                shape(2, i) = custom_points[i][2];
            }
            constraint->setShapes({shape});
        }

        return solver->addConstraint(constraint) >= 0;
    }

    /**
     * @brief Add bending constraint between two neighboring triangles
     * @param indices Vector of 4 vertex indices with shared-edge vertices first (id0, id1, id2, id3)
     * @param weight Weight of the constraint
     * @param min_range Minimum range factor (default: 1.0)
     * @param max_range Maximum range factor (default: 1.0)
     * @return true if constraint is added successfully
     */
    bool add_bending_constraint(std::vector<int> indices, double weight, 
                               double min_range = 1.0, double max_range = 1.0) {
        if (!is_valid()) {
            return false;
        }
        
        // Validate indices - need exactly 4 indices
        if (indices.size() != 4) {
            throw std::runtime_error("Bending constraint requires exactly 4 vertices");
        }
        
        // The shared-edge vertices come first. The opposite vertices id2 and
        // id3 complete the two neighboring triangles.
        // Order: id0, id1, id2, id3.
        
        // Create the bending constraint
        auto constraint = std::make_shared<ShapeOp::BendingConstraint>(
            indices, weight, solver->getPoints(), min_range, max_range);
        
        return solver->addConstraint(constraint) >= 0;
    }

    /**
     * @brief Add normal force with faces
     * @param faces_flat_array Flat array of face indices
     * @param face_sizes_array Array of face sizes
     * @param magnitude Magnitude of the force
     * @return true if force is added successfully
     */
    bool add_normal_force_with_faces(nb::ndarray<int> faces_flat_array, 
                                    nb::ndarray<int> face_sizes_array, 
                                    double magnitude) {
        if (!solver) {
            throw std::runtime_error("Solver not initialized");
        }

        // Get data pointers and dimensions
        const int* faces_flat_ptr = faces_flat_array.data();
        const int* face_sizes_ptr = face_sizes_array.data();
        
        size_t faces_flat_size = faces_flat_array.size();
        size_t face_count = face_sizes_array.size();
        
        // Convert the flat array representation to vector of vectors for faces
        std::vector<std::vector<int>> faces;
        size_t idx = 0;
        
        for (size_t i = 0; i < face_count; ++i) {
            int face_size = face_sizes_ptr[i];
            std::vector<int> face;
            
            for (int j = 0; j < face_size; ++j) {
                if (idx < faces_flat_size) {
                    face.push_back(faces_flat_ptr[idx++]);
                } else {
                    throw std::runtime_error("Face index out of bounds");
                }
            }
            
            faces.push_back(face);
        }
        
        // Create the normal force
        auto force = std::make_shared<ShapeOp::NormalForce>(faces, magnitude);
        solver->addForces({force});
        return true;
    }

    /**
     * @brief Add vertex force (for individual vertices)
     * @param force_x X-component of the force
     * @param force_y Y-component of the force
     * @param force_z Z-component of the force
     * @param vertex_id ID of the vertex
     * @return true if force is added successfully
     */
    bool add_vertex_force(double force_x, double force_y, double force_z, int vertex_id) {
        if (!is_valid()) {
            return false;
        }
        
        if (vertex_id < 0 || vertex_id >= solver->getPoints().cols()) {
            throw std::runtime_error("Vertex index out of bounds");
        }
        
        // Create a force vector
        ShapeOp::Vector3 force(force_x, force_y, force_z);
        
        // Create a vertex force and add it directly to the solver using addForces
        std::shared_ptr<ShapeOp::Force> vertex_force = std::make_shared<ShapeOp::VertexForce>(force, vertex_id);
        solver->addForces(vertex_force);
        
        return true;
    }

    /**
     * @brief Add gravity force to all vertices
     * @param force_x X-component of the gravity force
     * @param force_y Y-component of the gravity force
     * @param force_z Z-component of the gravity force
     * @return true if force is added successfully
     */
    bool add_gravity_force(double force_x, double force_y, double force_z) {
        if (!is_valid()) {
            return false;
        }
        
        // Create a force vector
        ShapeOp::Vector3 force(force_x, force_y, force_z);
        
        // Create a gravity force and add it directly to the solver
        std::shared_ptr<ShapeOp::Force> gravity_force = std::make_shared<ShapeOp::GravityForce>(force);
        solver->addForces(gravity_force);
        
        return true;
    }
};

//╔═══════════════════════════════════════════════════════════════════════════╗
//║                        PYTHON MODULE DEFINITION                           ║
//╚═══════════════════════════════════════════════════════════════════════════╝

// Define the module with a more explicit name to avoid conflicts
NB_MODULE(_shapeop, m) {
    // Give a clear docstring about this module
    m.doc() = "ShapeOp dynamic solver binding";
    
    // Define the solver class with a unique name
    nb::class_<SolverWrapper>(m, "SolverWrapper")
        .def(nb::init<>())
        .def("set_points", &SolverWrapper::set_points)
        .def("get_points", &SolverWrapper::get_points)
        .def("add_closeness_constraint", &SolverWrapper::add_closeness_constraint)
        .def("add_closeness_constraint_with_position", &SolverWrapper::add_closeness_constraint_with_position)
        .def("add_edge_strain_constraint", &SolverWrapper::add_edge_strain_constraint)
        .def("add_shrinking_edge_constraint", &SolverWrapper::add_shrinking_edge_constraint)
        .def("add_circle_constraint", &SolverWrapper::add_circle_constraint)
        .def("add_plane_constraint", &SolverWrapper::add_plane_constraint)
        .def("add_similarity_constraint", &SolverWrapper::add_similarity_constraint)
        .def("add_regular_polygon_constraint", &SolverWrapper::add_regular_polygon_constraint)
        .def("add_shape_constraint", &SolverWrapper::add_shape_constraint)
        .def("add_bending_constraint", &SolverWrapper::add_bending_constraint)
        .def("add_normal_force_with_faces", &SolverWrapper::add_normal_force_with_faces)
        .def("add_vertex_force", &SolverWrapper::add_vertex_force)
        .def("add_gravity_force", &SolverWrapper::add_gravity_force)
        .def("initialize", &SolverWrapper::initialize)
        .def("solve", &SolverWrapper::solve);
}
