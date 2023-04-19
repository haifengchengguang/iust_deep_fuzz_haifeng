"""
PDF OBJ 8laf4
- New in laf4
-- SampleFuzz Algorithm add.
-- creation date: 13970414
- New in laf3
-- Implement learn and fuzz model and sample fuzz algorithm (version 2)
-- For generate objects
- New in version 8
-- Fuzzing back to generate_and_fuzz method.
-- Perplexity and cross entropy add to metrics list.
-- Use some Keras backend to reset model graph and state.
-- Lets pdf_file_incremental_update_4.py call the generate_and_fuzz method.
- New in version 7
-- Use for bidirectional LSTM model, model=model9
- New in version 6
-- Train with 256 LSTM search, model=model_8
-- Train on large dataset for first time!
-New in version 5:
-- Data generator fixed.
-- Train on large dataset for first time!
-New in version 4:
-- Changing the data generator method for use with model.fit_generator()
-New in version 3:
-- Add support for training in large dataset with the help of python generators.
-- Add callbacks to log most of training time events.
-- File and directory now mange by code in appropriate manner for each train run.
-- Add class FileFormatFuzz to do learn and fuzz process in one script.
-- Note: The ability of training small dataset in memory with model.fit() method was include in version 3.

"""

from __future__ import print_function

__version__ = '0.8.1'
__author__ = 'Morteza'

import sys
import os
import datetime
import random
import numpy as np

from keras import backend as K
from keras.models import load_model
from keras.optimizers import RMSprop, Adam
#from keras.utils.vis_utils import plot_model
#from tensorflow.keras.optimizers import RMSprop,Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard, CSVLogger, LambdaCallback
from keras.utils import plot_model

import pdf_object_preprocess as preprocess
from config import learning_config
import deep_models


def cross_entropy(y_true, y_pred):
    """
    Compute cross_entropy loss metric

    :param y_true:
    :param y_pred:
    :return:
    """
    return K.categorical_crossentropy(y_true, y_pred)


def spars_cross_entropy(y_true, y_pred):
    return K.sparse_categorical_crossentropy(y_true, y_pred)


def perplexity(y_true, y_pred):
    """
    Compute perplexity metric

    :param y_true:
    :param y_pred:
    :return:
    """
    ce = K.categorical_crossentropy(y_true, y_pred)
    # pp = K.pow(np.e, ce)  # Or 2?
    # pp = K.pow(2., ce)  # Or np.e
    pp = K.exp(ce)
    # print('Perplexity value in perplexity function: ', K.eval(pp))
    return pp


class FileFormatFuzzer(object):
    """
    Main class for learn and fuzz process
    """
    def __init__(self, maxlen=85, step=1, batch_size=128):
        """

        :param maxlen:
        :param step:
        :param batch_size:
        """
        # os.chdir('./')

        # learning hyper-parameters
        self.maxlen = maxlen
        self.step = step
        self.batch_size = batch_size

        self.text_all = ''
        self.text_training = ''
        self.text_validation = ''
        self.text_test = ''

        self.chars = None
        self.char_indices = None
        self.indices_char = None

        # self.model = None
        K.reset_uids()
        K.clear_session()

        self.load_dataset()

    def define_model(self, input_dim, output_dim):
        """
        Build the model: a single LSTM layer # we need to deep it # now is deep :)
        :param input_dim:
        :param output_dim:
        :return:
        """
        model, model_name = deep_models.model7_laf(input_dim, output_dim)
        return model, model_name

    def load_dataset(self):
        """ Load all 3 part of each dataset and building dictionary index """
        if learning_config['dataset_size'] == 'small':
            self.text_training = preprocess.load_from_file(learning_config['small_training_set_path'])
            self.text_validation = preprocess.load_from_file(learning_config['small_validation_set_path'])
            self.text_test = preprocess.load_from_file(learning_config['small_testing_set_path'])
        elif learning_config['dataset_size'] == 'medium':
            self.text_training = preprocess.load_from_file(learning_config['medium_training_set_path'])
            self.text_validation = preprocess.load_from_file(learning_config['medium_validation_set_path'])
            self.text_test = preprocess.load_from_file(learning_config['medium_testing_set_path'])
        elif learning_config['dataset_size'] == 'large':
            self.text_training = preprocess.load_from_file(learning_config['large_training_set_path'])
            self.text_validation = preprocess.load_from_file(learning_config['large_validation_set_path'])
            self.text_test = preprocess.load_from_file(learning_config['large_testing_set_path'])
        self.text_all = self.text_training + self.text_validation + self.text_test
        print('Total corpus length:', len(self.text_all))
        self.chars = sorted(list(set(self.text_all)))
        print('Total corpus chars:', len(self.chars))
        # print(chars)

        # Building dictionary index
        print('Building dictionary index ...')
        self.char_indices = dict((c, i) for i, c in enumerate(self.chars))
        # print(char_indices)
        self.indices_char = dict((i, c) for i, c in enumerate(self.chars))
        # print(indices_char)

    # Generate samples from dataset base on learn and fuzz formula
    def generate_samples(self, text):
        """Cut the text in semi-redundant sequences of maxlen characters"""
        sentences = []  # List of all sentence as input
        next_chars = []  # List of all next chars as labels
        for i in range(0, (round(len(text) / self.maxlen)) - self.step, self.step):  # arg2 why this?
            # sentences.append(text[i: i + self.maxlen])
            sentences.append(text[i * self.maxlen: (i + self.step) * self.maxlen])
            # print(sentences)
            # print((i + self.step) * self.maxlen)
            next_chars.append(text[(i + self.step) * self.maxlen])
            # print(next_chars)
        print('Number of semi sequences or samples:', len(sentences))
        # input()
        return sentences, next_chars

    def data_generator(self, sentences, next_chars):
        """
        Batch data generator for large dataset not fit completely in memory
        # Index j now increase Shuffle

        :param sentences:
        :param next_chars:
        :return:
        """
        j = random.randint(0, len(sentences) - (self.batch_size+1))
        # print('Vectorization...')
        while True:
            # Fix generator :))
            x = np.zeros((self.batch_size, self.maxlen, len(self.chars)), dtype=np.bool)
            y = np.zeros((self.batch_size, len(self.chars)), dtype=np.bool)
            # j = random.randint(0, len(sentences) - (self.batch_size + 1))
            next_chars2 = next_chars[j: j + self.batch_size]  ## F...:)
            for i, one_sample in enumerate(sentences[j: j + self.batch_size]):
                for t, char in enumerate(one_sample):
                    x[i, t, self.char_indices[char]] = 1
                y[i, self.char_indices[next_chars2[i]]] = 1

            yield (x, y)
            # yield self.generate_single_batch(sentences, next_chars)
            j += self.batch_size
            if j > (len(sentences) - (self.batch_size+1)):
                j = random.randint(0, len(sentences) - (self.batch_size+1))

    def data_generator_validation(self, sentences, next_chars):
        """
                Batch data generator for large dataset not fit completely in memory
                # Index j now increase sequentially (validation don't need to shuffle)

                :param sentences:
                :param next_chars:
                :return:
                """
        j = 0
        # print('Vectorization...')
        while True:
            # Fix generator :))
            x = np.zeros((self.batch_size, self.maxlen, len(self.chars)), dtype=np.bool)
            y = np.zeros((self.batch_size, len(self.chars)), dtype=np.bool)
            # j = random.randint(0, len(sentences) - (self.batch_size + 1))
            next_chars2 = next_chars[j: j + self.batch_size]  ## F...:)
            for i, one_sample in enumerate(sentences[j: j + self.batch_size]):
                for t, char in enumerate(one_sample):
                    x[i, t, self.char_indices[char]] = 1
                y[i, self.char_indices[next_chars2[i]]] = 1

            yield (x, y)
            # yield self.generate_single_batch(sentences, next_chars)
            j += self.batch_size
            if j > (len(sentences) - (self.batch_size + 1)):
                j = 0

    def data_generator_in_memory(self, sentences, next_chars):
        """All data generate for small dataset fit completely in memory"""
        x = np.zeros((len(sentences), self.maxlen, len(self.chars)), dtype=np.bool)
        y = np.zeros((len(sentences), len(self.chars)), dtype=np.bool)
        for i, one_sample in enumerate(sentences):
            for t, char in enumerate(one_sample):
                x[i, t, self.char_indices[char]] = 1
            y[i, self.char_indices[next_chars[i]]] = 1
        return x, y

    def train(self,
              epochs=1,
              trained_model=None,
              trained_model_name='trained_model_wn'):
        """
        Create and train deep model

        :param epochs: Specify number of epoch for training.
        :param
        :
        :return: Nothing.
        """
        # Start time of training
        dt = datetime.datetime.now().strftime('_date_%Y-%m-%d_%H-%M-%S_')

        print('Generate training samples ...')
        sentences_training, next_chars_training = self.generate_samples(self.text_training + self.text_test)
        print('Generate validations samples ...')
        sentences_validation, next_chars_validation = self.generate_samples(self.text_validation)

        print('Build and compile model ...')
        model = None
        model_name = None
        if trained_model is None:
            model, model_name = self.define_model((self.maxlen, len(self.chars)), len(self.chars))
        else:
            model = trained_model
            model_name = trained_model_name
        optimizer = RMSprop(lr=0.01)  # [0.001, 0.01, 0.02, 0.05, 0.1]
        optimizer = Adam(lr=0.0001)  # Reduce from 0.001 to 0.0001 for model_10
        model.compile(optimizer=optimizer,
                      loss='categorical_crossentropy',
                      # metrics=['accuracy']
                      metrics=['accuracy', cross_entropy, perplexity])

        print(model_name, ' summary ...')
        model.summary()

        print(model_name, ' count_params ...')
        print(model.count_params())
        # input()

        print('Set #5 callback ...')
        # callback #1 EarlyStopping
        # monitor= 'val_loss' or monitor='loss'?
        model_early_stopping = EarlyStopping(monitor='loss', min_delta=0.01, patience=5, verbose=1, mode='auto')

        # callback #2 ModelCheckpoint
        # Create a directory for each training process to keep model checkpoint in .h5 format
        dir_name = './model_checkpoint/pdfs/' + model_name + dt + 'epochs_' + str(epochs) + '/'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        file_name = dir_name + model_name + dt + 'epoch_{epoch:02d}_val_loss_{val_loss:.4f}.h5'
        model_checkpoint = ModelCheckpoint(file_name, verbose=1)

        # callback #3 TensorBoard
        dir_name = './logs_tensorboard/pdfs/' + model_name + dt + 'epochs_' + str(epochs) + '/'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        model_tensorboard = TensorBoard(log_dir=dir_name, histogram_freq=0, batch_size=self.batch_size,
                                        write_graph=True, write_grads=False, write_images=True, embeddings_freq=0,
                                        embeddings_layer_names=None, embeddings_metadata=None)

        # callback #4 CSVLogger
        # Create a directory and an empty csv file within to save mode csv log.
        dir_name = './logs_csv/pdfs/' + model_name + dt + 'epochs_' + str(epochs) + '/'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        file_name = dir_name + model_name + dt + '_epochs_' + str(epochs) + '_step_' + str(self.step) + '.csv'
        open(file_name, mode='a', newline='').close()
        model_csv_logger = CSVLogger(file_name, separator=',', append=False)

        # callback #5 LambdaCallback
        dir_name = './generated_results/pdfs/' + model_name + dt + 'epochs_' + str(epochs) + '/'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        def on_epoch_end(epoch, logs):
            nonlocal model
            nonlocal epochs
            nonlocal model_name
            nonlocal dir_name
            print('Sampling model and save results ... ')
            self.generate_and_fuzz_new_samples(model=model,
                                               model_name=model_name,
                                               epochs=epochs,
                                               current_epoch=epoch,
                                               dir_name=dir_name
                                               )

        generate_and_fuzz_new_samples_callback = LambdaCallback(on_epoch_begin=None,
                                                                on_epoch_end=on_epoch_end,
                                                                on_batch_begin=None,
                                                                on_batch_end=None,
                                                                on_train_begin=None,
                                                                on_train_end=None
                                                                )

        if learning_config['dataset_size'] == 'small':  # very_small
            print('Start training on small dataset ...')
            x, y = self.data_generator_in_memory(sentences_training, next_chars_training)
            model.fit(x, y,
                      batch_size=self.batch_size,
                      epochs=epochs,
                      validation_split=0.2,
                      shuffle=True,
                      callbacks=[model_checkpoint,
                                 model_tensorboard,
                                 model_csv_logger,
                                 generate_and_fuzz_new_samples_callback]
                      )
        else:
            print('Build training and validation data generators ...')
            training_data_generator = self.data_generator(sentences_training, next_chars_training)
            validation_data_generator = self.data_generator_validation(sentences_validation, next_chars_validation)

            # x, y = next(training_data_generator)
            # print(x)
            # print('+'*75)
            # print(y)
            # print('#'*50)
            # x, y = next(training_data_generator)
            # print(x)
            # print('+' * 75)
            # print(y)
            # print('#' * 50)

            # input()

            print('Start training on large dataset ...')
            model.fit_generator(generator=training_data_generator,
                                # steps_per_epoch=200,
                                steps_per_epoch=len(sentences_training) // self.batch_size,  # 1000,
                                validation_data=validation_data_generator,
                                validation_steps=len(sentences_validation) // (self.batch_size*2),  # 100,
                                # validation_steps=10,
                                use_multiprocessing=False,
                                workers=1,
                                epochs=epochs,
                                shuffle=True,
                                callbacks=[model_checkpoint,
                                           model_tensorboard,
                                           model_csv_logger,
                                           generate_and_fuzz_new_samples_callback]
                                )

    # end of train method
    # --------------------------------------------------------------------

    def generate_and_fuzz_new_samples(self,
                                      model=None,
                                      model_name='model_1',
                                      epochs=1,
                                      current_epoch=1,
                                      dir_name=None):
        """
        sampling the model and generate new object
        :param model: The model which is training.
        :param model_name: Name of model (base on hyperparameters config in deep_model.py file) e.g. [model_1, model_2,
        ...]
        :param epochs: Number of total epochs of training, e.g. 10,20,30,40,50 or 60
        :param current_epoch: Number of current epoch
        :param dir_name: root directory for this running.
        :return: Nothing
        """

        # End time of current epoch
        dt = datetime.datetime.now().strftime('_date_%Y-%m-%d_%H-%M-%S')
        dir_name = dir_name + 'epoch_' + str(current_epoch) + dt + '/'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # Fuzzing hyper-parameters

        diversities = [i*0.10 for i in range(1, 20, 2)]
        # diversities = [0.2, 0.5, 1.0, 1.2, 1.5, 1.8]
        # diversities = [0.5, 1.0, 1.5]  # for sou and for mou
        diversities = [1.0]

        generated_obj_total = 100  # [5, 10, 100, 1000, 3000, 10000] {1000-1100 for sou and 3000-3100 for muo, 10000 for fuzz testing}
        generated_obj_with_same_prefix = 10  # [1, 5, 10, 20, 40] {10 for sou and 20 for mou}
        generated_obj_max_allowed_len = 400  # Choose max allowed len for object randomly
        exclude_from_fuzzing_set = {'s', 't', 'r', 'e', 'a', 'm'}  # set(['s', 't', 'r', 'e', 'a', 'm'])

        # Learn and fuzz paper hyper-parameters
        t_fuzz = 0.9  # For comparision with p_fuzz where p_fuzz is a random number (if p_fuzz > t_fuzz)
        p_t = 0.9  # 0.9 and more for format fuzzing; 0.5 and less than 0.5 for data fuzzing. Now format fuzzing.

        # End of fuzzing hyper-parameters

        testset_objects_list = preprocess.get_list_of_object(self.text_test)
        testset_object_gt_maxlen_list = []
        for obj in testset_objects_list:
            if len(obj) > self.maxlen+len(' endobj'):
                testset_object_gt_maxlen_list.append(obj)
        print('len filtered test-set: ', len(testset_object_gt_maxlen_list))
        generated_total = ''
        for diversity in diversities:
            generated_total = ''
            for q in range(round(generated_obj_total/generated_obj_with_same_prefix)):

                obj_index = random.randint(0, len(testset_object_gt_maxlen_list) - 1)
                # obj_index = 0
                generated_obj_counter = 0
                generated_obj_len = 0
                generated = ''
                stop_condition = False
                endobj_attach_manually = False
                # print()
                print('-- Diversity:', diversity)

                obj_prefix = str(testset_object_gt_maxlen_list[obj_index])[0: self.maxlen]
                generated += obj_prefix
                # prob_vals = '1 ' * self.maxlen
                # learnt_grammar = obj_prefix

                print('--- Generating ts_text with seed:\n "' + obj_prefix + '"')
                sys.stdout.write(generated)

                if generated.endswith('endobj'):
                    generated_obj_counter += 1

                if generated_obj_counter > generated_obj_with_same_prefix:
                    stop_condition = True

                while not stop_condition:
                    if(generated.endswith(' ')):
                        x_pred = np.zeros((1, self.maxlen, len(self.chars)))
                        for t, char in enumerate(obj_prefix):
                            x_pred[0, t, self.char_indices[char]] = 1.

                        preds = model.predict(x_pred, verbose=0)[0]
                        next_index, prob, preds2 = self.sample(preds, diversity)
                        next_char = self.indices_char[next_index]
                        # next_char_for_prefix = next_char

                        ###### Fuzzing section we don't need it yet!

                        p_fuzz = random.random()
                        if p_fuzz > t_fuzz and preds2[next_index] > p_t:
                            next_index = np.argmin(preds2)
                            # print('((Fuzz!))')
                        next_char = self.indices_char[next_index]
                        next_char_for_prefix = next_char

                        ###### End of fuzzing section

                        obj_prefix = obj_prefix[1:] + next_char_for_prefix
                        generated += next_char_for_prefix  # next_char
                        sys.stdout.write(generated)
                        generated_obj_len += 1
                    else:
                        # print("生成中间字符")
                        x_pred = np.zeros((1, self.maxlen, len(self.chars)))
                        for t, char in enumerate(obj_prefix):
                            x_pred[0, t, self.char_indices[char]] = 1.
                        preds = model.predict(x_pred, verbose=0)[0]
                        next_index, prob, preds2 = self.sample(preds, diversity)
                        next_char = self.indices_char[next_index]
                        next_char_for_prefix = next_char

                        ###### End of fuzzing section

                        obj_prefix = obj_prefix[1:] + next_char_for_prefix
                        generated += next_char_for_prefix  # next_char
                        sys.stdout.write(generated)
                        generated_obj_len += 1
                    if generated.endswith('endobj'):
                        generated_obj_counter += 1
                        generated_obj_len = 0
                    elif (generated.endswith('endobj') is False) and \
                            (generated_obj_len > generated_obj_max_allowed_len):
                        # Attach '\nendobj\n' manually, and reset obj_prefix
                        generated += '\nendobj\n'
                        generated_obj_counter += 1
                        generated_obj_len = 0
                        endobj_attach_manually = True

                    if generated_obj_counter >= generated_obj_with_same_prefix:  # Fix: Change > to >= (13970315)
                        stop_condition = True
                    elif endobj_attach_manually:
                        # Reset prefix:
                        # Here we need to modify obj_prefix because we manually change the generated_obj!
                        # Below we add this new repair:

                        # obj_prefix = obj_prefix[len('\nendobj\n'):] + '\nendobj\n'

                        # Instead of modify obj_prefix we can reset prefix if we found that 'endobj' dose not generate
                        # automatically. It seems to be better option, so we do this:
                        # obj_index = random.randint(0, len(testset_object_gt_maxlen_list) - 1)
                        obj_index = 0
                        obj_prefix = str(testset_object_gt_maxlen_list[obj_index])[0: self.maxlen]
                        generated += obj_prefix
                        endobj_attach_manually = False

                    # sys.stdout.write(next_char)
                    # sys.stdout.flush()
                    # print()
                sys.stdout.write(generated)
                generated_total += generated + '\n'
            # save generated_result to file inside program

            file_name = model_name \
                        + '_diversity_' + repr(diversity) \
                        + '_epochs_' + repr(epochs) \
                        + '_step_' + repr(self.step) \
                        + '.txt'
            preprocess.save_to_file(dir_name + file_name, generated_total)
            # preprocess.save_to_file(dir_name + file_name + 'probabilities.txt', prob_vals)
            # preprocess.save_to_file(dir_name + file_name + 'learntgrammar.txt',learnt_grammar)
            print('Diversity %s save to file successfully.' % diversity)
        print("-----")
        print(generated_total)
        print("-----")
        print('End of generation method.')
        print('Starting new epoch ...')
        return generated_total

    # Lower temperature will cause the model to make more likely,
    # but also more boring and conservative predictions.
    def sample(self, preds, temperature=1.0):
        """
        Helper function to sample an index from a probability array
        :param preds:
        :param temperature:
        :return:
        """

        # print('raw predictions = ', preds)
        preds = np.asarray(preds).astype('float64')

        preds = np.log(preds) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)

        # Sampling with numpy functions:
        probas = np.random.multinomial(1, preds, 1)
        # print()
        # print('sanitize predictions = ', preds)
        return np.argmax(probas), probas, preds

    def no_sample(self):
        pass

    def sample_space(self):
        pass

    def save_model_plot(self, model, epochs):
        """
        Save the model architecture plot.
        :param model:
        :param epochs:
        :return:
        """
        dt = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S_')
        # plot the model
        plot_model(model, to_file='./modelpic/date_' + dt + 'epochs_' + str(epochs) + '.png',
                   show_shapes=True, show_layer_names=True)

    def load_model_and_generate(self, model_name='model7_laf', epochs=50):
        dt = datetime.datetime.now().strftime('_date_%Y-%m-%d_%H-%M-%S')
        dir_name = './generated_results/pdfs/' + model_name + dt + 'epochs_' + str(epochs) + '/'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        model = load_model('./model_checkpoint/best_models/'
                           'model7_laf_date_2018-06-19_12-23-39_epoch_50_val_loss_0.7242.h5',
                           compile=False)
        optimizer = Adam(lr=0.0001)  # Reduce from 0.001 to 0.0001 for model_10
        model.compile(optimizer=optimizer,
                      loss='categorical_crossentropy',
                      # metrics=['accuracy']
                      metrics=['accuracy'])

        seq = self.generate_and_fuzz_new_samples(model=model,
                                      model_name=model_name,
                                      epochs=epochs,
                                      current_epoch=50,
                                      dir_name=dir_name)

        list_of_obj = preprocess.get_list_of_object(seq=seq, is_sort=False)
        return list_of_obj

    def get_model_summary(self):
        print('Get model summary ...')
        model, model_name = self.define_model((self.maxlen, len(self.chars)), len(self.chars))
        print(model_name, ' summary ...')
        model.summary()
        print(model_name, ' count_params ...')
        print(model.count_params())


def main(argv):
    """ The main function to call train() method"""
    epochs = 100
    fff = FileFormatFuzzer(maxlen=50, step=1, batch_size=128)
    # trained_model_dir = './model_checkpoint/best_models/'
    # trained_model_file_name = 'model_7_date_2018-05-14_21-44-21_epoch_65_val_loss_0.3335.h5'
    # trained_model_path = trained_model_dir + trained_model_file_name
    # trained_model = load_model(trained_model_path, compile=False)

    # Train deep model from first or continue training for previous trained model.
    # Trained model pass as argument.
    # fff.train(epochs=epochs,
    #           trained_model=trained_model,
    #           trained_model_name='model_7-1'
    #           )
    # fff.get_model_summary()
    list_of_obj = fff.load_model_and_generate()
    print('Len list_of_obj', len(list_of_obj))

    print('Training complete successfully on %s epochs' % epochs)


if __name__ == "__main__":
    main(sys.argv)
