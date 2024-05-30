import localsolver
import sys
import math
import tracemalloc
tracemalloc.start()
def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]


def main(instance_file, str_time_limit, sol_file):
    #
    # Read instance data
    #
    nb_customers, horizon_length, capacity, start_level_supplier, production_rate_supplier, \
        holding_cost_supplier, start_level, max_level, demand_rate, holding_cost, \
        dist_matrix_data, dist_supplier_data = read_input_irp(instance_file)

    with localsolver.LocalSolver() as ls:
        #
        # Declare the optimization model
        #
        model = ls.model

        # Quantity of product delivered at each discrete time instant of
        # the planning time horizon to each customer
        delivery = [[model.float(0, capacity) for i in range(nb_customers)]
                    for _ in range(horizon_length)]

        # Sequence of customers visited at each discrete time instant of
        # the planning time horizon
        route = [model.list(nb_customers) for t in range(horizon_length)]

        # Customers receive products only if they are visited
        is_delivered = [[model.contains(route[t], i) for i in range(nb_customers)]
                        for t in range(horizon_length)]

        # Create distance as an array to be able to access it with an "at" operator
        dist_matrix = model.array()
        for i in range(nb_customers):
            dist_matrix.add_operand(model.array(dist_matrix_data[i]))

        dist_supplier = model.array(dist_supplier_data)

        dist_routes = [None for _ in range(horizon_length)]

        for t in range(horizon_length):
            sequence = route[t]
            c = model.count(sequence)

            # Distance traveled at instant t
            dist_lambda = model.lambda_function(
                lambda i:
                    model.at(
                        dist_matrix,
                        sequence[i - 1],
                        sequence[i]))
            dist_routes[t] = model.iif(
                c > 0,
                dist_supplier[sequence[0]]
                + model.sum(model.range(1, c), dist_lambda)
                + dist_supplier[sequence[c - 1]],
                0)

        # Stockout constraints at the supplier
        inventory_supplier = [None for _ in range(horizon_length + 1)]
        inventory_supplier[0] = start_level_supplier
        for t in range(1, horizon_length + 1):
            inventory_supplier[t] = inventory_supplier[t - 1] - model.sum(
                delivery[t - 1][i] for i in range(nb_customers)) + production_rate_supplier
            if t != horizon_length:
                model.constraint(
                    inventory_supplier[t] >= model.sum(delivery[t][i]
                                                       for i in range(nb_customers)))

        # Stockout constraints at the customers
        inventory = [[None for _ in range(horizon_length + 1)] for _ in range(nb_customers)]
        for i in range(nb_customers):
            inventory[i][0] = start_level[i]
            for t in range(1, horizon_length + 1):
                inventory[i][t] = inventory[i][t - 1] + delivery[t - 1][i] - demand_rate[i]
                model.constraint(inventory[i][t] >= 0)

        for t in range(horizon_length):
            # Capacity constraints
            model.constraint(
                model.sum((delivery[t][i]) for i in range(nb_customers)) <= capacity)

            # Maximum level constraints
            for i in range(nb_customers):
                model.constraint(delivery[t][i] <= max_level[i] - inventory[i][t])
                model.constraint(delivery[t][i] <= max_level[i] * is_delivered[t][i])

        # Total inventory cost at the supplier
        total_cost_inventory_supplier = holding_cost_supplier * model.sum(
            inventory_supplier[t] for t in range(horizon_length + 1))

        # Total inventory cost at customers
        total_cost_inventory = model.sum(model.sum(
            holding_cost[i] * inventory[i][t] for t in range(horizon_length + 1))
            for i in range(nb_customers))

        # Total transportation cost
        total_cost_route = model.sum(dist_routes[t] for t in range(horizon_length))

        # Objective: minimize the sum of all costs
        objective = total_cost_inventory_supplier + total_cost_inventory + total_cost_route
        model.minimize(objective)

        model.close()

        # Parameterize the solver
        ls.param.time_limit = int(str_time_limit)

        ls.solve()

        #
        # Write the solution in a file with the following format :
        # - total distance run by the vehicle
        # - the nodes visited at each time step (omitting the start/end at the supplier)
        #
        if len(sys.argv) >= 3:
            with open(sol_file, 'w') as f:
                f.write("%d\n" % (total_cost_route.value))
                for t in range(horizon_length):
                    for customer in route[t].value:
                        f.write("%d " % (customer + 1))
                    f.write("\n")


# The input files follow the "Archetti" format
def read_input_irp(filename):
    file_it = iter(read_elem(filename))
    nb_customers = int(next(file_it)) - 1
    horizon_length = int(next(file_it))
    capacity = int(next(file_it))
    nb_vehicles = int(next(file_it))
    capacity = capacity*nb_vehicles
    start_level = [None] * nb_customers
    max_level = [None] * nb_customers
    min_level = [None] * nb_customers
    demand_rate = [None] * nb_customers
    holding_cost = [None] * nb_customers
    next(file_it)
    start_level_supplier = int(next(file_it))
    production_rate_supplier = int(next(file_it))
    holding_cost_supplier = float(next(file_it))
    for i in range(nb_customers):
        a = float(next(file_it))
        start_level[i] = int(next(file_it))
        max_level[i] = int(next(file_it))
        min_level[i] = int(next(file_it))
        demand_rate[i] = int(next(file_it))
        holding_cost[i] = float(next(file_it))

    distance_matrix = distance_matrix = [[None for i in range(nb_customers)] for j in range(nb_customers)]
    distance_supplier = [None] * nb_customers
    next(file_it)
    for i in range(nb_customers):
        distance_supplier[i] = int(float(next(file_it)))
    for i in range(nb_customers):
        a = float(next(file_it))
        for j in range(nb_customers):
            if(j<nb_customers):
               distance_matrix[i][j] = int(float(next(file_it)))
    return nb_customers, horizon_length, capacity, start_level_supplier, \
        production_rate_supplier, holding_cost_supplier, start_level, max_level, \
        demand_rate, holding_cost, distance_matrix, distance_supplier


# Compute the distance matrix
def compute_distance_matrix(x_coord, y_coord):
    nb_customers = len(x_coord)
    distance_matrix = [[None for i in range(nb_customers)] for j in range(nb_customers)]
    for i in range(nb_customers):
        distance_matrix[i][i] = 0
        for j in range(nb_customers):
            dist = compute_dist(x_coord[i], x_coord[j], y_coord[i], y_coord[j])
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist
    return distance_matrix


# Compute the distances to the supplier
def compute_distance_supplier(x_coord_supplier, y_coord_supplier, x_coord, y_coord):
    nb_customers = len(x_coord)
    distance_supplier = [None] * nb_customers
    for i in range(nb_customers):
        dist = compute_dist(x_coord_supplier, x_coord[i], y_coord_supplier, y_coord[i])
        distance_supplier[i] = dist
    return distance_supplier


def compute_dist(xi, xj, yi, yj):
    return round(math.sqrt(math.pow(xi - xj, 2) + math.pow(yi - yj, 2)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python irp.py input_file [output_file] [time_limit]")
        sys.exit(1)

    instance_file = sys.argv[1]
    sol_file = sys.argv[2] if len(sys.argv) > 2 else None
    str_time_limit = sys.argv[3] if len(sys.argv) > 3 else "20"

    main(instance_file, str_time_limit, sol_file)
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
    tracemalloc.stop()
#python irp.py C:\Users\Admin\Downloads\absH6high1n50.txt
#python irp.py C:\Users\Admin\Testcase.txt
#python C:\Users\Admin\Downloads\irp\irp.py C:\Users\Admin\test.txt
#python C:\Users\Admin\Downloads\irp\irp.py C:\Users\Admin\Testcase.txt
#set PYTHONPATH=D:\localsolver_12_5\bin\python
#python C:\Users\Admin\irp.py C:\Users\Admin\Downloads\absH6high1n50.txt