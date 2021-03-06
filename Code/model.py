import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam
from keras.layers import Lambda, Conv2D, MaxPooling2D, Dropout, Dense, Flatten
from utils import INPUT_SHAPE, batch_generator
import argparse
import os

np.random.seed(0)

def load_data(args):
    data_df = pd.read_csv(os.path.join(args.data_dir, 'driving_log.csv'), names=['center', 'left', 'right', 'steering', 'speed', 'throttle', 'break'])
    x = data_df[['center', 'left', 'right']].values
    y = data_df['steering'].values

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = args.test_size, random_state = 0)

    return x_train, x_test, y_train, y_test

def printline():
    print('-'*30)

def build_model(args):
    model = Sequential()
    
    # Image normalization layer
    # Number x/127.5-1.0 is based on NVIDEA's research paper 
    # layer desaturate and color correct the image    
    # Exponential Linear Unit takes care of vanishing gradient
     
    model.add(Lambda(lambda x: x/127.5-1.0, input_shape=INPUT_SHAPE))
    
    # Convolution layer: 5x5, filter: 24, strides = 2x2, activation: ELU
    model.add(Conv2D(24, 5, 5, activation='elu', subsample=(2,2)))
    
    # Convolution layer: 5x5, filter: 36, strides = 2x2, activation: ELU
    model.add(Conv2D(36, 5, 5, activation='elu', subsample=(2,2)))
    
    # Convolution layer: 5x5, filter: 48, strides = 2x2, activation: ELU
    model.add(Conv2D(48, 5, 5, activation='elu', subsample=(2,2)))
    
    # Convolution layer: 3x3, filter: 64, strides = 2x2, activation: ELU
    model.add(Conv2D(64, 3, 3, activation='elu', subsample=(1,1)))
    
    # Convolution layer: 3x3, filter: 64, strides = 2x2, activation: ELU
    model.add(Conv2D(64, 3, 3, activation='elu', subsample=(1,1)))
    
    # # Convolution layer: 5x5, filter: 24, strides = 2x2, activation: ELU
    # model.add(Conv2D(24, 5, 5, activation='elu', strides=(2,2)))
 
    # # Convolution layer: 5x5, filter: 36, strides = 2x2, activation: ELU
    # model.add(Conv2D(36, 5, 5, activation='elu', strides=(2,2)))
    
    # # Convolution layer: 5x5, filter: 48, strides = 2x2, activation: ELU
    # model.add(Conv2D(48, 5, 5, activation='elu', strides=(2,2)))
    
    # # Convolution layer: 3x3, filter: 64, strides = 2x2, activation: ELU
    # model.add(Conv2D(64, 3, 3, activation='elu', strides=(1,1)))
    
    # # Convolution layer: 3x3, filter: 64, strides = 2x2, activation: ELU
    # model.add(Conv2D(64, 3, 3, activation='elu', strides=(1,1)))

    # Drop out layer: 0.5, flatten to add fully connected NN
    model.add(Dropout(args.keep_prob))
    model.add(Flatten())

    # add fully connected neural network layers
    model.add(Dense(100, activation='elu'))
    model.add(Dense(50, activation='elu'))
    model.add(Dense(10, activation='elu'))
    model.add(Dense(1))
    model.summary()
    
    return model

def train_model(model, args, X_train, X_test, y_train, y_test):
    checkpoint = ModelCheckpoint('model-{epoch:03d}.h5', monitor='val_loss', verbose=0, save_best_only=args.save_best_only, mode='auto')
    model.compile(loss='mean_squared_error', optimizer=Adam(lr=args.learning_rate))

    model.fit_generator(batch_generator(args.data_dir, X_train, y_train, args.batch_size, False), 
        args.samples_per_epoch, args.nb_epoch, max_q_size=1, 
        validation_data=batch_generator(args.data_dir, X_test, y_test, args.batch_size, False),
        nb_val_samples=len(X_test), callbacks=[checkpoint], verbose=1)

def save_best(s):
    s = s.lower()
    return s=='true' or s=='yes' or s=='1'

def main():
    parser = argparse.ArgumentParser(description='Self Driving Simulation Program')
    parser.add_argument('-d', help='data directory', dest='data_dir', type=str, default='data')
    parser.add_argument('-t', help='test size fraction', dest='test_size', type=float, default=0.2)
    parser.add_argument('-k', help='drop out probability', dest='keep_prob', type=float, default=0.5)
    parser.add_argument('-n', help='number of epochs', dest='nb_epoch', type=int, default=10)
    parser.add_argument('-s', help='samples per epoch', dest='samples_per_epoch', type=int, default=20000)
    parser.add_argument('-b', help='batch size', dest='batch_size', type=int, default=40)
    parser.add_argument('-o', help='save best models only', dest='save_best_only', type=save_best, default='true')
    parser.add_argument('-l', help='learning rate', dest='learning_rate', type=float, default=1.0e-4)
    args=parser.parse_args()

    printline()
    print('Parameters')
    printline()
    
    for key, val in vars(args).items():
        print('{:<20} :  {}'.format(key, val))
    printline()

    data = load_data(args)
    model = build_model(args)
    train_model(model, args, *data)

if __name__ == '__main__':
    main()