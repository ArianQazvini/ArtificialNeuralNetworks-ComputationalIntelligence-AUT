from layers.convolution2d import Conv2D
from layers.maxpooling2d import MaxPool2D
from layers.fullyconnected import FC

from activations import Activation, get_activation, Sigmoid, ReLU, LinearActivation, Tanh
import pickle
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
from random import shuffle


class Model:
    def __init__(self, arch, criterion, optimizer, name=None):
        """
        Initialize the model.
        args:
            arch: dictionary containing the architecture of the model
            criterion: loss
            optimizer: optimizer
            name: name of the model
        """
        if name is None:
            self.model = arch
            self.criterion = criterion
            self.optimizer = optimizer
            self.layers_names = list(arch.keys())
        else:
            self.model, self.criterion, self.optimizer, self.layers_names = self.load_model(name)

    def is_layer(self, layer):
        """
        Check if the layer is a layer.
        args:
            layer: layer to be checked
        returns:
            True if the layer is a layer, False otherwise
        """
        # TODO: Implement check if the layer is a layer
        if (type(layer) == MaxPool2D or type(layer) == FC or type(layer) == Conv2D):
            return True
        else:
            return False

    def is_activation(self, layer):
        """
        Check if the layer is an activation function.
        args:
            layer: layer to be checked
        returns:
            True if the layer is an activation function, False otherwise
        """
        # TODO: Implement check if the layer is an activation
        if (type(layer) == Sigmoid or type(layer) == LinearActivation or type(layer) == ReLU or type(layer) == Tanh):
            return True
        else:
            return False

    def forward(self, x):
        """
        Forward pass through the model.
        args:
            x: input to the model
        returns:
            output of the model
        """
        tmp = []
        A = x
        # TODO: Implement forward pass through the model
        # NOTICE: we have a pattern of layers and activations
        for l in range(0, len(self.layers_names), 2):
            Z = self.model[self.layers_names[l]].forward(A)
            tmp.append(np.copy(Z))  # hint add a copy of Z to tmp
            A = self.model[self.layers_names[l + 1]].forward(Z)
            tmp.append(np.copy(A))  # hint add a copy of A to tmp
        return tmp

    def backward(self, dAL, tmp, x):
        """
        Backward pass through the model.
        args:
            dAL: derivative of the cost with respect to the output of the model
            tmp: list containing the intermediate values of Z and A
            x: input to the model
        returns:
            gradients of the model
        """
        dA = dAL
        grads = {}
        # TODO: Implement backward pass through the model
        # NOTICE: we have a pattern of layers and activations
        # for from the end to the beginning of the tmp list
        for l in range(len(self.layers_names) - 1, -1, -2):
            if l > 2:
                Z, A = tmp[l - 1], tmp[l - 2]
            else:
                Z, A = tmp[l - 1], x
            dZ = self.model[self.layers_names[l]].backward(dA, Z)
            dA, grad = self.model[self.layers_names[l - 1]].backward(dZ, A)
            grads[self.layers_names[l - 1]] = grad
        return grads

    def update(self, grads):
        """
        Update the model.
        args:
            grads: gradients of the model
        """
        for name in self.layers_names:
            if self.is_layer(self.model[name]) and (type(self.model[name])!=MaxPool2D):  # hint check if the layer is a layer and also is not a maxpooling layer
                self.model[name].update_parameters(self.optimizer, grads[name])

    def one_epoch(self, x, y):
        """
        One epoch of training.
        args:
            x: input to the model
            y: labels
            batch_size: batch size
        returns:
            loss
        """
        # TODO: Implement one epoch of training
        tmp = self.forward(x)
        AL = tmp[-1]
        loss = self.criterion.compute(AL, y)
        dAL = self.criterion.backward(AL, y)
        grads = self.backward(dAL, tmp, x)
        self.update(grads)
        return loss

    def save(self, name):
        """
        Save the model.
        args:
            name: name of the model
        """
        with open(name, 'wb') as f:
            pickle.dump((self.model, self.criterion, self.optimizer, self.layers_names), f)

    def load_model(self, name):
        """
        Load the model.
        args:
            name: name of the model
        returns:
            model, criterion, optimizer, layers_names
        """
        with open(name, 'rb') as f:
            return pickle.load(f)

    def shuffle(self, m, shuffling):
        order = list(range(m))
        if shuffling:
            np.random.shuffle(order)
        return order

    def batch(self, X, y, batch_size, index, order):
        """
        Get a batch of data.
        args:
            X: input to the model
            y: labels
            batch_size: batch size
            index: index of the batch
                e.g: if batch_size = 3 and index = 1 then the batch will be from index [3, 4, 5]
            order: order of the data
        returns:
            bx, by: batch of data
        """
        # TODO: Implement batch
        start_index = (index) * batch_size
        last_index = (index + 1) * batch_size  # hint last index of the batch check for the last batch
        batch = order[start_index: last_index]
        batch_np = np.asarray(batch)
        # NOTICE: inputs are 4 dimensional or 2 demensional
        if (len(X.shape) == 2):
            bx = X[:,batch_np]
            by = y[:,batch_np]
            # by = y[:, batch]
            return bx, by
        else:
            # batch_np= batch_np.reshape(1,-1)
            bx = []
            by=[]
            for i in batch_np:
                bx.append(X[i,:,:,:])
                by.append(y[0][i])
            # bx = X[batch_np,:,:,:]
            # by = y[:,batch_np]
            temp_x = np.array(bx)
            temp_y = np.array(by).reshape(1,-1)
            return temp_x,temp_y

    def compute_loss(self, X, y, batch_size):
        """
        Compute the loss.
        args:
            X: input to the model
            y: labels
            Batch_Size: batch size
        returns:
            loss
        """
        # TODO: Implement compute loss
        if (len(X.shape) == 4):
            m = X.shape[0]
        else:
            m = X.shape[1]
        order = self.shuffle(m, False)
        cost = 0
        for b in range(m // batch_size):
            bx, by = self.batch(X, y, batch_size, b, order)
            tmp = self.forward(bx)
            AL = tmp[-1]
            cost += self.criterion.compute_cost(AL, y)(m // batch_size)
        return cost

    def train(self, X, y, epochs, val=None, batch_size=3, shuffling=False, verbose=1, save_after=None):
        """
        Train the model.
        args:
            X: input to the model
            y: labels
            epochs: number of epochs
            val: validation data
            batch_size: batch size
            shuffling: if True shuffle the data
            verbose: if 1 print the loss after each epoch
            save_after: save the model after training
        """
        # TODO: Implement training
        train_cost = []
        val_cost = []
        # NOTICE: if your inputs are 4 dimensional m = X.shape[0] else m = X.shape[1]
        if (len(X.shape) == 4):
            m = X.shape[0]
        else:
            m = X.shape[1]
        for e in tqdm(range(1, epochs + 1)):
            order = self.shuffle(m, shuffling)
            cost = 0
            for b in range(m // batch_size):
                bx, by = self.batch(X, y, batch_size, b, order)
                cost += self.one_epoch(bx, by) / (m // batch_size)
            train_cost.append(cost)
            if val is not None:
                val_cost.append(self.compute_loss(X, y, batch_size))
            if verbose != False:
                if e % verbose == 0:
                    print("Epoch {}: train cost = {}".format(e, cost))
                if val is not None:
                    print("Epoch {}: val cost = {}".format(e, val_cost[-1]))
        if save_after is not None:
            self.save(save_after)
        return train_cost, val_cost

    def predict(self, X):
        """
        Predict the output of the model.
        args:
            X: input to the model
        returns:
            predictions
        """
        # TODO: Implement prediction
        tmp = self.forward(X)
        return tmp[-1]